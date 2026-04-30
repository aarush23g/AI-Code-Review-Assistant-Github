from __future__ import annotations

from typing import Any

from app.core.config import get_settings


def choose_review_strategy(pr_context: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()

    total_files = len(pr_context.get("files", []))
    reviewable_files = len(pr_context.get("reviewable_files", []))
    total_chunks = len(pr_context.get("review_chunks", []))

    if reviewable_files == 0 or total_chunks == 0:
        return {
            "mode": "skip",
            "reason": "no_reviewable_files",
            "max_chunks": 0,
        }

    if (
        total_chunks >= settings.large_pr_chunk_threshold
        or total_files >= settings.large_pr_file_threshold
    ):
        return {
            "mode": "summary_limited",
            "reason": "large_pr",
            "max_chunks": min(settings.max_review_chunks, total_chunks),
        }

    return {
        "mode": "full_summary",
        "reason": "normal",
        "max_chunks": min(settings.max_review_chunks, total_chunks),
    }
