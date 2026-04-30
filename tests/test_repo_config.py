from app.review.repo_config import build_runtime_review_config, parse_repo_review_config


def test_parse_repo_review_config_valid() -> None:
    raw = """
mode: security
min_inline_comment_confidence: 0.9
max_inline_comments: 2
ignored_paths:
  - docs/
  - migrations/
summary_max_chunks: 6
"""
    config = parse_repo_review_config(raw)

    assert config is not None
    assert config.mode == "security"
    assert config.min_inline_comment_confidence == 0.9
    assert config.max_inline_comments == 2
    assert config.ignored_paths == ["docs/", "migrations/"]
    assert config.summary_max_chunks == 6


def test_parse_repo_review_config_invalid_mode_falls_back_to_quick() -> None:
    raw = """
mode: random_mode
"""
    config = parse_repo_review_config(raw)

    assert config is not None
    assert config.mode == "quick"


def test_parse_repo_review_config_returns_none_for_invalid_yaml() -> None:
    raw = "mode: [security"
    config = parse_repo_review_config(raw)

    assert config is None


def test_build_runtime_review_config_uses_defaults_when_missing() -> None:
    runtime = build_runtime_review_config(
        None,
        default_mode="quick",
        default_min_inline_comment_confidence=0.85,
        default_max_inline_comments=3,
        default_summary_max_chunks=12,
    )

    assert runtime["mode"] == "quick"
    assert runtime["min_inline_comment_confidence"] == 0.85
    assert runtime["max_inline_comments"] == 3
    assert runtime["ignored_paths"] == []
    assert runtime["summary_max_chunks"] == 12
