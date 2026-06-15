import asyncio
import os
import sqlite3
from app.core.config import get_settings
from app.storage.metrics_store import ReviewMetricsStore

async def main():
    settings = get_settings()
    db_path = settings.review_metrics_db_path
    print(f"Using database: {db_path}")

    # Initialize store
    store = ReviewMetricsStore(db_path)

    # Prepare mock run data
    mock_data = {
        "repository": "test/repo",
        "pull_number": 42,
        "status": "completed",
        "strategy": "full_summary",
        "mode": "security",
        "reason": None,
        "file_count": 5,
        "reviewable_file_count": 3,
        "chunk_count": 10,
        "summary_issue_count": 2,
        "inline_finding_count": 4,
        "inline_comment_count": 2,
        "prompt_tokens": 1200,
        "completion_tokens": 400,
        "total_tokens": 1600,
        "duration_ms": 1500.5,
        "model": "deepseek-ai/deepseek-v4-flash",
    }

    # Record the run
    run_id = await store.record_review_run(mock_data)
    print(f"Successfully recorded review run with ID: {run_id}")

    # Query directly from database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM review_runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()

    if row:
        print("DATABASE CHECK SUCCESS!")
        print(f"Repository: {row['repository']}")
        print(f"Pull Number: {row['pull_number']}")
        print(f"Status: {row['status']}")
        print(f"Total Tokens: {row['total_tokens']}")
        print(f"Created At: {row['created_at']}")
    else:
        print("DATABASE CHECK FAILED: Row not found!")

if __name__ == "__main__":
    asyncio.run(main())
