from unittest.mock import AsyncMock

import pytest

from app.github.client import GitHubAPIClient
from app.schemas.review import (
    InlineReviewFinding,
    InlineReviewResult,
    PRSummaryReview,
    TopIssue,
)
from app.services.review_service import ReviewService
from app.storage.metrics_store import ReviewMetricsStore


@pytest.mark.asyncio
async def test_fetch_pull_request_context() -> None:
    github_client = GitHubAPIClient()
    github_client.get_pull_request = AsyncMock(
        return_value={
            "number": 14,
            "title": "Add webhook support",
            "body": "Initial PR",
            "state": "open",
            "html_url": "https://github.com/example/repo/pull/14",
            "user": {"login": "aaruush"},
            "base": {"ref": "main"},
            "head": {"ref": "feature/webhook", "sha": "abc123"},
        }
    )
    github_client.get_pull_request_files = AsyncMock(
        return_value=[
            {
                "filename": "app/main.py",
                "status": "modified",
                "additions": 12,
                "deletions": 2,
                "changes": 14,
                "patch": "@@ -1,2 +1,12 @@\n-print('old')\n+print('new')\n",
                "blob_url": "https://github.com/example/repo/blob/main/app/main.py",
                "raw_url": "https://raw.githubusercontent.com/example/repo/main/app/main.py",
            },
            {
                "filename": "docs/readme.md",
                "status": "modified",
                "additions": 4,
                "deletions": 1,
                "changes": 5,
                "patch": "@@ -1 +1 @@\n-old\n+new\n",
                "blob_url": None,
                "raw_url": None,
            },
        ]
    )
    github_client.get_repository_file_content = AsyncMock(
        return_value="""
mode: security
ignored_paths:
  - docs/
summary_max_chunks: 6
max_inline_comments: 2
min_inline_comment_confidence: 0.9
"""
    )

    service = ReviewService(github_client=github_client, llm_reviewer=AsyncMock())

    result = await service.fetch_pull_request_context(
        repository_full_name="example/repo",
        pull_number=14,
        installation_id=12345,
    )

    assert result["pull_request"]["number"] == 14
    assert result["pull_request"]["title"] == "Add webhook support"
    assert result["pull_request"]["head_sha"] == "abc123"
    assert len(result["files"]) == 2
    assert len(result["reviewable_files"]) == 1
    assert result["reviewable_files"][0]["filename"] == "app/main.py"
    assert result["runtime_config"]["mode"] == "security"
    assert result["runtime_config"]["summary_max_chunks"] == 6


@pytest.mark.asyncio
async def test_generate_pr_summary_review_completed() -> None:
    mocked_llm = AsyncMock()
    mocked_llm.generate_pr_summary_review = AsyncMock(
        return_value={
            "review": PRSummaryReview(
                summary="This PR adds webhook support.",
                top_issues=[
                    TopIssue(
                        severity="high",
                        title="Missing signature error coverage",
                        explanation="The webhook path may miss edge-case validation tests.",
                        filename="app/api/routes/webhook.py",
                        confidence=0.92,
                    )
                ],
                risky_files=["app/api/routes/webhook.py"],
                suggested_tests=["Add a test for malformed GitHub signature headers."],
            ),
            "usage": {
                "prompt_tokens": 111,
                "completion_tokens": 55,
                "total_tokens": 166,
            },
            "model": "gpt-4.1-mini",
        }
    )

    service = ReviewService(github_client=AsyncMock(), llm_reviewer=mocked_llm)

    pr_context = {
        "pull_request": {
            "number": 14,
            "title": "Add webhook support",
            "body": "Initial PR",
            "state": "open",
            "base_ref": "main",
            "head_ref": "feature/webhook",
        },
        "files": [{"filename": "app/api/routes/webhook.py"}],
        "reviewable_files": [{"filename": "app/api/routes/webhook.py"}],
        "review_chunks": [
            {
                "chunk_id": "app/api/routes/webhook.py::chunk-1",
                "filename": "app/api/routes/webhook.py",
                "chunk_index": 1,
                "total_chunks": 1,
                "patch": "@@ -1 +1 @@\n-print('old')\n+print('new')\n",
                "additions": 1,
                "deletions": 1,
                "changes": 2,
                "status": "modified",
                "blob_url": None,
                "raw_url": None,
            }
        ],
        "runtime_config": {
            "mode": "security",
            "summary_max_chunks": 4,
            "max_inline_comments": 2,
            "min_inline_comment_confidence": 0.9,
            "ignored_paths": [],
        },
    }

    result = await service.generate_pr_summary_review(pr_context)

    assert result["status"] == "completed"
    assert result["strategy"] == "full_summary"
    assert result["review"]["summary"] == "This PR adds webhook support."
    assert len(result["review"]["top_issues"]) == 1
    assert result["model"] == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_generate_pr_summary_review_skips_when_no_reviewable_files() -> None:
    service = ReviewService(github_client=AsyncMock(), llm_reviewer=AsyncMock())

    pr_context = {
        "pull_request": {
            "number": 14,
            "title": "Lockfile update",
            "body": "Update dependencies",
            "state": "open",
            "base_ref": "main",
            "head_ref": "deps/update",
        },
        "files": [{"filename": "package-lock.json"}],
        "reviewable_files": [],
        "review_chunks": [],
        "runtime_config": {
            "mode": "quick",
            "summary_max_chunks": 12,
            "max_inline_comments": 3,
            "min_inline_comment_confidence": 0.85,
            "ignored_paths": [],
        },
    }

    result = await service.generate_pr_summary_review(pr_context)

    assert result["status"] == "skipped"
    assert result["reason"] == "no_reviewable_files"
    assert result["review"] is None


@pytest.mark.asyncio
async def test_generate_inline_review_findings_returns_filtered_findings() -> None:
    mocked_llm = AsyncMock()
    mocked_llm.generate_inline_findings = AsyncMock(
        return_value={
            "result": InlineReviewResult(
                findings=[
                    InlineReviewFinding(
                        severity="high",
                        title="Missing validation",
                        explanation="Input is not validated.",
                        filename="app/main.py",
                        line=11,
                        confidence=0.95,
                    ),
                    InlineReviewFinding(
                        severity="low",
                        title="Minor style note",
                        explanation="Naming can be improved.",
                        filename="app/main.py",
                        line=14,
                        confidence=0.20,
                    ),
                ]
            ),
            "usage": None,
            "model": "gpt-4.1-mini",
        }
    )

    service = ReviewService(github_client=AsyncMock(), llm_reviewer=mocked_llm)

    pr_context = {
        "reviewable_files": [
            {
                "filename": "app/main.py",
                "patch": "@@ -10,2 +10,3 @@\n old_line\n+validated_input = validate(data)\n unchanged\n",
            }
        ],
        "review_chunks": [
            {
                "chunk_id": "app/main.py::chunk-1",
                "filename": "app/main.py",
                "chunk_index": 1,
                "total_chunks": 1,
                "patch": "@@ -10,2 +10,3 @@\n old_line\n+validated_input = validate(data)\n unchanged\n",
                "additions": 1,
                "deletions": 1,
                "changes": 2,
                "status": "modified",
                "blob_url": None,
                "raw_url": None,
            }
        ],
        "runtime_config": {
            "mode": "maintainability",
            "summary_max_chunks": 12,
            "max_inline_comments": 2,
            "min_inline_comment_confidence": 0.9,
            "ignored_paths": [],
        },
    }

    findings = await service.generate_inline_review_findings(pr_context)

    assert len(findings) == 1
    assert findings[0]["title"] == "Missing validation"


@pytest.mark.asyncio
async def test_publish_pr_summary_review_posts_comment_when_no_existing_bot_comment() -> (
    None
):
    github_client = GitHubAPIClient()
    github_client.list_issue_comments = AsyncMock(return_value=[])
    github_client.create_issue_comment = AsyncMock(
        return_value={
            "id": 999,
            "html_url": "https://github.com/example/repo/pull/14#issuecomment-999",
        }
    )

    service = ReviewService(github_client=github_client, llm_reviewer=AsyncMock())

    review = {
        "summary": "This PR adds webhook support.",
        "top_issues": [],
        "risky_files": [],
        "suggested_tests": [],
    }

    result = await service.publish_pr_summary_review(
        repository_full_name="example/repo",
        pull_number=14,
        installation_id=12345,
        review=review,
    )

    assert result["status"] == "posted"
    assert result["comment_id"] == 999


@pytest.mark.asyncio
async def test_publish_pr_summary_review_updates_when_existing_bot_comment_found() -> (
    None
):
    github_client = GitHubAPIClient()
    github_client.list_issue_comments = AsyncMock(
        return_value=[
            {
                "id": 123,
                "body": "<!-- ai-code-review-assistant -->\nExisting review",
            }
        ]
    )
    github_client.update_issue_comment = AsyncMock(
        return_value={
            "id": 123,
            "html_url": "https://github.com/example/repo/pull/14#issuecomment-123",
        }
    )
    github_client.create_issue_comment = AsyncMock()

    service = ReviewService(github_client=github_client, llm_reviewer=AsyncMock())

    review = {
        "summary": "Updated review summary.",
        "top_issues": [],
        "risky_files": [],
        "suggested_tests": [],
    }

    result = await service.publish_pr_summary_review(
        repository_full_name="example/repo",
        pull_number=14,
        installation_id=12345,
        review=review,
    )

    assert result["status"] == "updated"
    assert result["comment_id"] == 123
    github_client.update_issue_comment.assert_called_once()
    github_client.create_issue_comment.assert_not_called()


@pytest.mark.asyncio
async def test_publish_pr_summary_review_skips_when_existing_bot_comment_has_no_id() -> (
    None
):
    github_client = GitHubAPIClient()
    github_client.list_issue_comments = AsyncMock(
        return_value=[
            {
                "body": "<!-- ai-code-review-assistant -->\nExisting review without id",
            }
        ]
    )
    github_client.update_issue_comment = AsyncMock()
    github_client.create_issue_comment = AsyncMock()

    service = ReviewService(github_client=github_client, llm_reviewer=AsyncMock())

    review = {
        "summary": "Updated review summary.",
        "top_issues": [],
        "risky_files": [],
        "suggested_tests": [],
    }

    result = await service.publish_pr_summary_review(
        repository_full_name="example/repo",
        pull_number=14,
        installation_id=12345,
        review=review,
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "existing_review_comment_missing_id"
    github_client.update_issue_comment.assert_not_called()
    github_client.create_issue_comment.assert_not_called()


@pytest.mark.asyncio
async def test_publish_inline_review_comments_posts_comments() -> None:
    github_client = GitHubAPIClient()
    github_client.create_pull_request_review_comment = AsyncMock(
        return_value={"id": 777}
    )

    service = ReviewService(github_client=github_client, llm_reviewer=AsyncMock())

    findings = [
        {
            "severity": "high",
            "title": "Missing validation",
            "explanation": "Input is not validated.",
            "filename": "app/main.py",
            "line": 12,
            "confidence": 0.95,
        }
    ]

    result = await service.publish_inline_review_comments(
        repository_full_name="example/repo",
        pull_number=14,
        installation_id=12345,
        commit_id="abc123",
        findings=findings,
    )

    assert len(result) == 1
    assert result[0]["status"] == "posted"
    assert result[0]["comment_id"] == 777


def test_record_review_metrics(tmp_path) -> None:
    metrics_store = ReviewMetricsStore(str(tmp_path / "metrics.sqlite3"))

    service = ReviewService(
        github_client=AsyncMock(),
        llm_reviewer=AsyncMock(),
        metrics_store=metrics_store,
    )

    pr_context = {
        "files": [{"filename": "app/main.py"}],
        "reviewable_files": [{"filename": "app/main.py"}],
        "review_chunks": [{"chunk_id": "chunk-1"}],
        "runtime_config": {"mode": "security"},
    }

    review_result = {
        "status": "completed",
        "reason": "normal",
        "strategy": "full_summary",
        "review": {
            "top_issues": [{"title": "Issue"}],
        },
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
        "model": "gpt-4.1-mini",
    }

    run_id = service.record_review_metrics(
        repository_full_name="example/repo",
        pull_number=14,
        pr_context=pr_context,
        review_result=review_result,
        inline_findings=[{"title": "Inline issue"}],
        inline_publish_results=[{"status": "posted"}],
        duration_ms=123.4,
    )

    assert run_id >= 1

    summary = metrics_store.get_summary()
    assert summary["total_runs"] == 1
    assert summary["total_tokens"] == 150
    assert summary["total_inline_comments"] == 1
