"""
Evaluation runner for the AI Code Review Assistant.

Loads code snippets from the evaluation dataset, wraps them as fake PR diffs,
runs them through the LLMReviewer, and compares results against ground-truth
labels. Outputs results to evaluation/results/run_<timestamp>.json.

Usage:
    python -m evaluation.evaluate --mode security
    python -m evaluation.evaluate --model gpt-4.1-mini --mode quick
    python -m evaluation.evaluate --mode security --rate-limit 2.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.review.llm_reviewer import LLMReviewer

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

DATASET_DIR = Path(__file__).parent / "dataset"
RESULTS_DIR = Path(__file__).parent / "results"


def load_dataset() -> tuple[list[dict], list[dict]]:
    """Load vulnerable and safe snippet datasets."""
    with open(DATASET_DIR / "vulnerable_snippets.json", encoding="utf-8") as f:
        vulnerable = json.load(f)
    with open(DATASET_DIR / "safe_snippets.json", encoding="utf-8") as f:
        safe = json.load(f)
    return vulnerable, safe


def snippet_to_patch(snippet: dict) -> str:
    """Convert a code snippet into a unified diff patch format."""
    lines = snippet["code"].split("\n")
    patch_lines = [f"@@ -0,0 +1,{len(lines)} @@"]
    for line in lines:
        patch_lines.append(f"+{line}")
    return "\n".join(patch_lines)


def build_pr_context(snippet: dict, mode: str) -> dict[str, Any]:
    """Wrap a snippet as a fake PR context for the reviewer."""
    filename = f"app/{snippet['id'].replace('-', '_')}.py"
    patch = snippet_to_patch(snippet)

    return {
        "pull_request": {
            "number": 1,
            "title": f"Evaluation snippet: {snippet['id']}",
            "body": snippet.get("description", "Evaluation test"),
            "state": "open",
            "base_ref": "main",
            "head_ref": "eval/test",
            "head_sha": "eval123",
        },
        "files": [{"filename": filename}],
        "reviewable_files": [{"filename": filename, "patch": patch}],
        "review_chunks": [
            {
                "chunk_id": f"{filename}::chunk-1",
                "filename": filename,
                "chunk_index": 1,
                "total_chunks": 1,
                "patch": patch,
                "additions": len(snippet["code"].split("\n")),
                "deletions": 0,
                "changes": len(snippet["code"].split("\n")),
                "status": "added",
                "blob_url": None,
                "raw_url": None,
            }
        ],
        "runtime_config": {
            "mode": mode,
            "summary_max_chunks": 12,
            "max_inline_comments": 5,
            "min_inline_comment_confidence": 0.5,
            "ignored_paths": [],
        },
    }


async def _run_summary(llm: LLMReviewer, pr_context: dict, mode: str) -> dict[str, Any]:
    """Run summary review, return result dict."""
    from app.review.prompt_builder import SYSTEM_PROMPT, build_pr_summary_review_prompt

    start = time.perf_counter()
    try:
        user_prompt = build_pr_summary_review_prompt(pr_context=pr_context, mode=mode)
        summary_result = await llm.generate_pr_summary_review(
            SYSTEM_PROMPT, user_prompt
        )
        latency = time.perf_counter() - start
        review = summary_result.get("review")

        out: dict[str, Any] = {
            "found_issues": [],
            "latency_ms": round(latency * 1000, 2),
            "usage": summary_result.get("usage"),
            "model": summary_result.get("model"),
        }

        if review:
            review_obj = review
            if hasattr(review_obj, "model_dump"):
                review_obj = review_obj.model_dump()
            issues = review_obj.get("top_issues", [])
            out["found_issues"] = issues
            out["issue_count"] = len(issues)
        else:
            out["issue_count"] = 0
        return out

    except Exception as e:
        latency = time.perf_counter() - start
        return {"error": str(e), "latency_ms": round(latency * 1000, 2)}


async def _run_inline(
    llm: LLMReviewer, pr_context: dict, mode: str, snippet: dict, is_vulnerable: bool
) -> dict[str, Any]:
    """Run inline findings, return result dict."""
    from app.review.prompt_builder import (
        INLINE_FINDINGS_SYSTEM_PROMPT,
        build_inline_findings_prompt,
    )

    start = time.perf_counter()
    try:
        chunk = pr_context["review_chunks"][0]
        user_prompt = build_inline_findings_prompt(review_chunk=chunk, mode=mode)
        inline_result = await llm.generate_inline_findings(
            INLINE_FINDINGS_SYSTEM_PROMPT, user_prompt
        )
        latency = time.perf_counter() - start
        findings_obj = inline_result.get("result")

        out: dict[str, Any] = {
            "findings": [],
            "latency_ms": round(latency * 1000, 2),
            "usage": inline_result.get("usage"),
        }

        if findings_obj:
            if hasattr(findings_obj, "model_dump"):
                findings_obj = findings_obj.model_dump()
            findings = findings_obj.get("findings", [])
            out["findings"] = findings
            out["finding_count"] = len(findings)

            if is_vulnerable and snippet.get("vulnerable_lines"):
                found_lines = {f.get("line") for f in findings if f.get("line")}
                expected_lines = set(snippet["vulnerable_lines"])
                matched = found_lines & expected_lines
                out["line_accuracy"] = (
                    len(matched) / len(expected_lines) if expected_lines else 0.0
                )
        else:
            out["finding_count"] = 0
        return out

    except Exception as e:
        latency = time.perf_counter() - start
        return {"error": str(e), "latency_ms": round(latency * 1000, 2)}


async def evaluate_snippet(
    llm: LLMReviewer,
    snippet: dict,
    mode: str,
    is_vulnerable: bool,
) -> dict[str, Any]:
    """Run a single snippet through the LLM reviewer and collect results.

    Summary and inline calls run concurrently for ~2x speed improvement.
    """
    pr_context = build_pr_context(snippet, mode)

    result: dict[str, Any] = {
        "snippet_id": snippet["id"],
        "is_vulnerable": is_vulnerable,
        "vulnerability_type": snippet.get("vulnerability_type"),
        "expected_severity": snippet.get("severity"),
        "expected_lines": snippet.get("vulnerable_lines", []),
    }

    # Run both API calls concurrently
    summary_out, inline_out = await asyncio.gather(
        _run_summary(llm, pr_context, mode),
        _run_inline(llm, pr_context, mode, snippet, is_vulnerable),
    )

    result["summary"] = summary_out
    result["inline"] = inline_out
    return result


async def run_evaluation(
    mode: str = "security",
    model: str | None = None,
    base_url: str | None = None,
    rate_limit: float = 1.0,
) -> dict[str, Any]:
    """Run the full evaluation suite."""
    settings = get_settings()
    if model:
        settings.openai_model = model
    if base_url:
        settings.openai_base_url = base_url

    llm = LLMReviewer()
    vulnerable, safe = load_dataset()

    logger.info(
        "Starting evaluation | mode=%s model=%s base_url=%s vulnerable=%d safe=%d",
        mode,
        llm.model,
        settings.openai_base_url or "default",
        len(vulnerable),
        len(safe),
    )

    results: list[dict[str, Any]] = []
    total = len(vulnerable) + len(safe)

    # Evaluate vulnerable snippets
    for i, snippet in enumerate(vulnerable, 1):
        logger.info("[%d/%d] Evaluating vulnerable: %s", i, total, snippet["id"])
        result = await evaluate_snippet(llm, snippet, mode, is_vulnerable=True)
        results.append(result)
        if i < total:
            await asyncio.sleep(rate_limit)

    # Evaluate safe snippets
    for j, snippet in enumerate(safe, 1):
        idx = len(vulnerable) + j
        logger.info("[%d/%d] Evaluating safe: %s", idx, total, snippet["id"])
        result = await evaluate_snippet(llm, snippet, mode, is_vulnerable=False)
        results.append(result)
        if idx < total:
            await asyncio.sleep(rate_limit)

    # Build run metadata
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    # Create a safe model label for the filename
    model_label = llm.model.replace("/", "_").replace(".", "-")
    run_data = {
        "run_id": f"run_{model_label}_{timestamp}",
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": mode,
        "model": llm.model,
        "base_url": settings.openai_base_url or "default",
        "dataset": {
            "vulnerable_count": len(vulnerable),
            "safe_count": len(safe),
        },
        "results": results,
    }

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"run_{model_label}_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2, default=str)

    logger.info("Results saved to %s", output_path)
    return run_data


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Code Review Evaluation Runner")
    parser.add_argument(
        "--mode",
        choices=["quick", "security", "maintainability"],
        default="security",
        help="Review mode to use",
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Override LLM model name"
    )
    parser.add_argument(
        "--base-url", type=str, default=None, help="Override OpenAI base URL"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds to wait between API calls (default: 1.0)",
    )
    args = parser.parse_args()

    asyncio.run(
        run_evaluation(
            mode=args.mode,
            model=args.model,
            base_url=args.base_url,
            rate_limit=args.rate_limit,
        )
    )


if __name__ == "__main__":
    main()
