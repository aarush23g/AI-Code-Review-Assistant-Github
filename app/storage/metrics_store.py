from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS review_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository TEXT NOT NULL,
    pull_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    strategy TEXT,
    mode TEXT,
    reason TEXT,
    file_count INTEGER DEFAULT 0,
    reviewable_file_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    summary_issue_count INTEGER DEFAULT 0,
    inline_finding_count INTEGER DEFAULT 0,
    inline_comment_count INTEGER DEFAULT 0,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    duration_ms REAL,
    model TEXT,
    created_at TEXT NOT NULL
);
"""


class ReviewMetricsStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(SCHEMA)
            conn.commit()

    def record_review_run(self, data: dict[str, Any]) -> int:
        created_at = datetime.now(UTC).isoformat()

        row = {
            "repository": data.get("repository"),
            "pull_number": data.get("pull_number"),
            "status": data.get("status"),
            "strategy": data.get("strategy"),
            "mode": data.get("mode"),
            "reason": data.get("reason"),
            "file_count": data.get("file_count", 0),
            "reviewable_file_count": data.get("reviewable_file_count", 0),
            "chunk_count": data.get("chunk_count", 0),
            "summary_issue_count": data.get("summary_issue_count", 0),
            "inline_finding_count": data.get("inline_finding_count", 0),
            "inline_comment_count": data.get("inline_comment_count", 0),
            "prompt_tokens": data.get("prompt_tokens"),
            "completion_tokens": data.get("completion_tokens"),
            "total_tokens": data.get("total_tokens"),
            "duration_ms": data.get("duration_ms"),
            "model": data.get("model"),
            "created_at": created_at,
        }

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO review_runs (
                    repository, pull_number, status, strategy, mode, reason,
                    file_count, reviewable_file_count, chunk_count,
                    summary_issue_count, inline_finding_count, inline_comment_count,
                    prompt_tokens, completion_tokens, total_tokens,
                    duration_ms, model, created_at
                )
                VALUES (
                    :repository, :pull_number, :status, :strategy, :mode, :reason,
                    :file_count, :reviewable_file_count, :chunk_count,
                    :summary_issue_count, :inline_finding_count, :inline_comment_count,
                    :prompt_tokens, :completion_tokens, :total_tokens,
                    :duration_ms, :model, :created_at
                )
                """,
                row,
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_summary(self) -> dict[str, Any]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            total_runs = conn.execute(
                "SELECT COUNT(*) AS count FROM review_runs"
            ).fetchone()["count"]

            total_tokens = conn.execute(
                "SELECT COALESCE(SUM(total_tokens), 0) AS value FROM review_runs"
            ).fetchone()["value"]

            avg_latency = conn.execute(
                "SELECT COALESCE(AVG(duration_ms), 0) AS value FROM review_runs"
            ).fetchone()["value"]

            total_inline_comments = conn.execute(
                "SELECT COALESCE(SUM(inline_comment_count), 0) AS value FROM review_runs"
            ).fetchone()["value"]

            skipped_runs = conn.execute(
                "SELECT COUNT(*) AS count FROM review_runs WHERE status = 'skipped'"
            ).fetchone()["count"]

        return {
            "total_runs": total_runs,
            "total_tokens": total_tokens,
            "avg_latency_ms": round(float(avg_latency), 2),
            "total_inline_comments": total_inline_comments,
            "skipped_runs": skipped_runs,
        }
