"""
Metrics API endpoint.

Exposes review metrics from the SQLite database for monitoring
and dashboard consumption.
"""

from __future__ import annotations

import logging
from typing import Any

import aiosqlite
from fastapi import APIRouter, Request

from app.core.config import get_settings

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = logging.getLogger(__name__)


@router.get("/summary")
async def get_metrics_summary(request: Request) -> dict[str, Any]:
    """Return a summary of review metrics."""
    settings = get_settings()
    db_path = settings.review_metrics_db_path

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Total reviews
        cursor = await db.execute("SELECT COUNT(*) AS count FROM review_runs")
        row = await cursor.fetchone()
        assert row is not None
        total_reviews = row["count"]

        # By status
        cursor = await db.execute(
            "SELECT status, COUNT(*) AS count FROM review_runs GROUP BY status"
        )
        reviews_by_status = {row["status"]: row["count"] async for row in cursor}

        # By mode
        cursor = await db.execute(
            "SELECT mode, COUNT(*) AS count FROM review_runs WHERE mode IS NOT NULL GROUP BY mode"
        )
        reviews_by_mode = {row["mode"]: row["count"] async for row in cursor}

        # Latency
        cursor = await db.execute(
            "SELECT COALESCE(AVG(duration_ms), 0) AS avg_latency FROM review_runs"
        )
        row = await cursor.fetchone()
        assert row is not None
        avg_latency = row["avg_latency"]

        # Tokens
        cursor = await db.execute(
            "SELECT COALESCE(SUM(total_tokens), 0) AS total, "
            "COALESCE(SUM(prompt_tokens), 0) AS prompt, "
            "COALESCE(SUM(completion_tokens), 0) AS completion "
            "FROM review_runs"
        )
        tokens = await cursor.fetchone()
        assert tokens is not None

        # Inline comments
        cursor = await db.execute(
            "SELECT COALESCE(SUM(inline_comment_count), 0) AS total FROM review_runs"
        )
        row = await cursor.fetchone()
        assert row is not None
        total_inline = row["total"]

        # Issues by severity (from summary_issue_count as proxy)
        cursor = await db.execute(
            "SELECT COALESCE(SUM(summary_issue_count), 0) AS total FROM review_runs"
        )
        row = await cursor.fetchone()
        assert row is not None
        total_issues = row["total"]

        # Recent reviews
        cursor = await db.execute(
            "SELECT repository, pull_number, status, mode, strategy, "
            "duration_ms, total_tokens, inline_comment_count, created_at "
            "FROM review_runs ORDER BY id DESC LIMIT 10"
        )
        recent = [dict(row) async for row in cursor]

        # Reviews over time (last 30 days, grouped by date)
        cursor = await db.execute(
            "SELECT DATE(created_at) AS date, COUNT(*) AS count "
            "FROM review_runs "
            "WHERE created_at >= DATE('now', '-30 days') "
            "GROUP BY DATE(created_at) ORDER BY date"
        )
        reviews_over_time = [
            {"date": row["date"], "count": row["count"]} async for row in cursor
        ]

        # Top repositories
        cursor = await db.execute(
            "SELECT repository, COUNT(*) AS count, "
            "COALESCE(SUM(total_tokens), 0) AS tokens "
            "FROM review_runs GROUP BY repository ORDER BY count DESC LIMIT 10"
        )
        top_repos = [dict(row) async for row in cursor]

    return {
        "total_reviews": total_reviews,
        "avg_latency_ms": round(float(avg_latency), 2),
        "total_tokens": tokens["total"],
        "prompt_tokens": tokens["prompt"],
        "completion_tokens": tokens["completion"],
        "total_inline_comments": total_inline,
        "total_issues_found": total_issues,
        "reviews_by_status": reviews_by_status,
        "reviews_by_mode": reviews_by_mode,
        "reviews_over_time": reviews_over_time,
        "top_repositories": top_repos,
        "recent_reviews": recent,
    }
