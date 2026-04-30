from app.review.orchestrator import choose_review_strategy


def test_choose_review_strategy_skips_when_no_reviewable_files() -> None:
    pr_context = {
        "files": [{"filename": "package-lock.json"}],
        "reviewable_files": [],
        "review_chunks": [],
    }

    result = choose_review_strategy(pr_context)

    assert result["mode"] == "skip"
    assert result["reason"] == "no_reviewable_files"
    assert result["max_chunks"] == 0


def test_choose_review_strategy_uses_limited_mode_for_large_pr() -> None:
    pr_context = {
        "files": [{"filename": f"file_{i}.py"} for i in range(30)],
        "reviewable_files": [{"filename": f"file_{i}.py"} for i in range(25)],
        "review_chunks": [{"chunk_id": f"chunk_{i}"} for i in range(22)],
    }

    result = choose_review_strategy(pr_context)

    assert result["mode"] == "summary_limited"
    assert result["reason"] == "large_pr"


def test_choose_review_strategy_uses_full_summary_for_normal_pr() -> None:
    pr_context = {
        "files": [{"filename": "app/main.py"}],
        "reviewable_files": [{"filename": "app/main.py"}],
        "review_chunks": [{"chunk_id": "chunk_1"}],
    }

    result = choose_review_strategy(pr_context)

    assert result["mode"] == "full_summary"
    assert result["reason"] == "normal"
