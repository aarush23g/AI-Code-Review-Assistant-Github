from app.storage.metrics_store import ReviewMetricsStore


def test_record_review_run_and_get_summary(tmp_path) -> None:
    db_path = tmp_path / "metrics.sqlite3"
    store = ReviewMetricsStore(str(db_path))

    run_id = store.record_review_run(
        {
            "repository": "example/repo",
            "pull_number": 14,
            "status": "completed",
            "strategy": "full_summary",
            "mode": "security",
            "reason": "normal",
            "file_count": 3,
            "reviewable_file_count": 2,
            "chunk_count": 4,
            "summary_issue_count": 1,
            "inline_finding_count": 2,
            "inline_comment_count": 1,
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "duration_ms": 250.5,
            "model": "gpt-4.1-mini",
        }
    )

    assert run_id >= 1

    summary = store.get_summary()

    assert summary["total_runs"] == 1
    assert summary["total_tokens"] == 150
    assert summary["avg_latency_ms"] == 250.5
    assert summary["total_inline_comments"] == 1
    assert summary["skipped_runs"] == 0


def test_metrics_summary_counts_skipped_runs(tmp_path) -> None:
    db_path = tmp_path / "metrics.sqlite3"
    store = ReviewMetricsStore(str(db_path))

    store.record_review_run(
        {
            "repository": "example/repo",
            "pull_number": 22,
            "status": "skipped",
            "strategy": "skip",
            "mode": "quick",
            "reason": "no_reviewable_files",
        }
    )

    summary = store.get_summary()

    assert summary["total_runs"] == 1
    assert summary["skipped_runs"] == 1
