from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from app.core.config import get_settings
from app.github.client import GitHubAPIClient
from app.github.comments import format_pr_summary_comment
from app.review.chunker import build_review_chunks
from app.review.diff_parser import filter_reviewable_files
from app.review.line_mapper import build_changed_line_map
from app.review.llm_reviewer import LLMReviewer
from app.review.orchestrator import choose_review_strategy
from app.review.post_processor import (
    normalize_inline_review_result,
    normalize_pr_summary_review,
    select_inline_findings,
)
from app.review.prompt_builder import (
    INLINE_FINDINGS_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_inline_findings_prompt,
    build_pr_summary_review_prompt,
)
from app.review.repo_config import build_runtime_review_config, parse_repo_review_config
from app.schemas.github import PullRequestDetails, PullRequestFile
from app.schemas.review import ReviewExecutionResult
from app.storage.metrics_store import ReviewMetricsStore
from app.storage.repository import find_existing_review_comment

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(
        self,
        github_client: GitHubAPIClient | None = None,
        llm_reviewer: LLMReviewer | None = None,
        metrics_store: ReviewMetricsStore | None = None,
    ) -> None:
        settings = get_settings()
        self.github_client = github_client or GitHubAPIClient()
        self.llm_reviewer = llm_reviewer or LLMReviewer()
        self.metrics_store = metrics_store or ReviewMetricsStore(
            settings.review_metrics_db_path
        )

    def record_review_metrics(
        self,
        *,
        repository_full_name: str,
        pull_number: int,
        pr_context: dict[str, Any],
        review_result: dict[str, Any],
        inline_findings: list[dict[str, Any]] | None = None,
        inline_publish_results: list[dict[str, Any]] | None = None,
        duration_ms: float | None = None,
    ) -> int:
        runtime_config = pr_context.get("runtime_config", {})
        review = review_result.get("review") or {}
        usage = review_result.get("usage") or {}

        data = {
            "repository": repository_full_name,
            "pull_number": pull_number,
            "status": review_result.get("status"),
            "strategy": review_result.get("strategy"),
            "mode": runtime_config.get("mode"),
            "reason": review_result.get("reason"),
            "file_count": len(pr_context.get("files", [])),
            "reviewable_file_count": len(pr_context.get("reviewable_files", [])),
            "chunk_count": len(pr_context.get("review_chunks", [])),
            "summary_issue_count": len(review.get("top_issues", [])),
            "inline_finding_count": len(inline_findings or []),
            "inline_comment_count": len(inline_publish_results or []),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "duration_ms": duration_ms,
            "model": review_result.get("model"),
        }

        return self.metrics_store.record_review_run(data)

    async def fetch_repo_review_config(
        self,
        repository_full_name: str,
        ref: str,
        installation_id: int,
    ) -> dict[str, object]:
        settings = get_settings()
        owner, repo = repository_full_name.split("/", 1)

        raw_content = await self.github_client.get_repository_file_content(
            owner=owner,
            repo=repo,
            path=".aireview.yml",
            ref=ref,
            installation_id=installation_id,
        )

        repo_config = parse_repo_review_config(raw_content)

        runtime_config = build_runtime_review_config(
            repo_config,
            default_mode=settings.default_review_mode,
            default_min_inline_comment_confidence=settings.min_inline_comment_confidence,
            default_max_inline_comments=settings.max_inline_comments,
            default_summary_max_chunks=settings.max_review_chunks,
        )

        return runtime_config

    async def fetch_pull_request_context(
        self,
        repository_full_name: str,
        pull_number: int,
        installation_id: int,
    ) -> dict[str, Any]:
        owner, repo = repository_full_name.split("/", 1)

        pr_data = await self.github_client.get_pull_request(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            installation_id=installation_id,
        )

        pr_files_data = await self.github_client.get_pull_request_files(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            installation_id=installation_id,
        )

        pr_details = PullRequestDetails(
            number=pr_data["number"],
            title=pr_data["title"],
            body=pr_data.get("body"),
            state=pr_data["state"],
            html_url=pr_data["html_url"],
            user_login=(pr_data.get("user") or {}).get("login"),
            base_ref=(pr_data.get("base") or {}).get("ref"),
            head_ref=(pr_data.get("head") or {}).get("ref"),
            head_sha=(pr_data.get("head") or {}).get("sha"),
        )

        runtime_config = await self.fetch_repo_review_config(
            repository_full_name=repository_full_name,
            ref=pr_details.head_sha or pr_details.head_ref or "HEAD",
            installation_id=installation_id,
        )

        pr_files = [
            PullRequestFile(
                filename=file["filename"],
                status=file["status"],
                additions=file.get("additions", 0),
                deletions=file.get("deletions", 0),
                changes=file.get("changes", 0),
                patch=file.get("patch"),
                blob_url=file.get("blob_url"),
                raw_url=file.get("raw_url"),
            )
            for file in pr_files_data
        ]

        reviewable_files = filter_reviewable_files(
            pr_files,
            ignored_paths=list(runtime_config.get("ignored_paths", [])),
        )
        review_chunks = build_review_chunks(reviewable_files)

        return {
            "pull_request": pr_details.model_dump(),
            "files": [file.model_dump() for file in pr_files],
            "reviewable_files": [file.model_dump() for file in reviewable_files],
            "review_chunks": [chunk.model_dump() for chunk in review_chunks],
            "runtime_config": runtime_config,
        }

    async def generate_pr_summary_review(
        self,
        pr_context: dict[str, Any],
    ) -> dict[str, Any]:
        strategy = choose_review_strategy(pr_context)

        if strategy["mode"] == "skip":
            return ReviewExecutionResult(
                status="skipped",
                reason=strategy["reason"],
                strategy=strategy["mode"],
                review=None,
                usage=None,
                model=None,
            ).model_dump()

        start = perf_counter()

        runtime_config = pr_context.get("runtime_config", {})
        mode = str(runtime_config.get("mode", "quick"))
        summary_max_chunks = int(
            runtime_config.get("summary_max_chunks", strategy["max_chunks"])
        )

        user_prompt = build_pr_summary_review_prompt(
            pr_context,
            max_chunks=min(strategy["max_chunks"], summary_max_chunks),
            mode=mode,
        )

        llm_result = await self.llm_reviewer.generate_pr_summary_review(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        raw_review = llm_result["review"]
        normalized_review = normalize_pr_summary_review(raw_review)

        duration_ms = round((perf_counter() - start) * 1000, 2)

        logger.info(
            "AI summary review generated | strategy=%s reason=%s mode=%s chunks=%s issues=%s duration_ms=%s model=%s usage=%s",
            strategy["mode"],
            strategy["reason"],
            mode,
            min(strategy["max_chunks"], summary_max_chunks),
            len(normalized_review.top_issues),
            duration_ms,
            llm_result.get("model"),
            llm_result.get("usage"),
        )

        return ReviewExecutionResult(
            status="completed",
            reason=strategy["reason"],
            strategy=strategy["mode"],
            review=normalized_review.model_dump(),
            usage=llm_result.get("usage"),
            model=llm_result.get("model"),
        ).model_dump()

    async def generate_inline_review_findings(
        self,
        pr_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        runtime_config = pr_context.get("runtime_config", {})
        mode = str(runtime_config.get("mode", "quick"))
        max_inline_comments = int(
            runtime_config.get("max_inline_comments", settings.max_inline_comments)
        )
        min_confidence = float(
            runtime_config.get(
                "min_inline_comment_confidence",
                settings.min_inline_comment_confidence,
            )
        )

        reviewable_files = pr_context.get("reviewable_files", [])
        changed_line_map = build_changed_line_map(reviewable_files)

        valid_filenames = {file["filename"] for file in reviewable_files}
        selected_chunks = pr_context.get("review_chunks", [])[
            : settings.max_review_chunks
        ]

        collected = []

        for chunk in selected_chunks:
            prompt = build_inline_findings_prompt(chunk, mode=mode)
            llm_result = await self.llm_reviewer.generate_inline_findings(
                system_prompt=INLINE_FINDINGS_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            normalized = normalize_inline_review_result(llm_result["result"])

            findings = select_inline_findings(
                normalized,
                valid_filenames,
                min_confidence=min_confidence,
                max_findings=max_inline_comments,
                changed_line_map=changed_line_map,
            )

            collected.extend(findings)

        deduped = []
        seen = set()

        for finding in collected:
            key = (
                finding.filename,
                finding.line,
                finding.title.strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(finding)

        deduped.sort(
            key=lambda item: (
                {"high": 3, "medium": 2, "low": 1}.get(item.severity, 0),
                item.confidence,
            ),
            reverse=True,
        )

        return [finding.model_dump() for finding in deduped[:max_inline_comments]]

    async def publish_pr_summary_review(
        self,
        repository_full_name: str,
        pull_number: int,
        installation_id: int,
        review: dict[str, Any],
    ) -> dict[str, Any]:
        owner, repo = repository_full_name.split("/", 1)

        existing_comments = await self.github_client.list_issue_comments(
            owner=owner,
            repo=repo,
            issue_number=pull_number,
            installation_id=installation_id,
        )

        comment_body = format_pr_summary_comment(
            review=review,
            repository_full_name=repository_full_name,
            pull_number=pull_number,
        )

        existing_bot_comment = find_existing_review_comment(existing_comments)

        if existing_bot_comment is not None:
            comment_id = existing_bot_comment.get("id")

            if comment_id is None:
                return {
                    "status": "skipped",
                    "reason": "existing_review_comment_missing_id",
                }

            updated_comment = await self.github_client.update_issue_comment(
                owner=owner,
                repo=repo,
                comment_id=int(comment_id),
                installation_id=installation_id,
                body=comment_body,
            )

            return {
                "status": "updated",
                "comment_id": updated_comment.get("id"),
                "html_url": updated_comment.get("html_url"),
            }

        created_comment = await self.github_client.create_issue_comment(
            owner=owner,
            repo=repo,
            issue_number=pull_number,
            installation_id=installation_id,
            body=comment_body,
        )

        return {
            "status": "posted",
            "comment_id": created_comment.get("id"),
            "html_url": created_comment.get("html_url"),
        }

    async def publish_inline_review_comments(
        self,
        repository_full_name: str,
        pull_number: int,
        installation_id: int,
        commit_id: str,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        owner, repo = repository_full_name.split("/", 1)

        published = []

        for finding in findings:
            body = (
                f"**[{finding['severity'].upper()}] {finding['title']}**\n\n"
                f"{finding['explanation']}\n\n"
                f"_Confidence: {finding['confidence']:.2f}_"
            )

            try:
                result = await self.github_client.create_pull_request_review_comment(
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                    installation_id=installation_id,
                    body=body,
                    commit_id=commit_id,
                    path=finding["filename"],
                    line=finding["line"],
                )
                published.append(
                    {
                        "status": "posted",
                        "filename": finding["filename"],
                        "line": finding["line"],
                        "comment_id": result.get("id"),
                    }
                )
            except Exception:
                logger.exception(
                    "Failed to publish inline comment | repo=%s pr=%s file=%s line=%s",
                    repository_full_name,
                    pull_number,
                    finding["filename"],
                    finding["line"],
                )

        return published
