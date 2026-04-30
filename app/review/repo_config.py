from __future__ import annotations

import logging

import yaml
from pydantic import ValidationError

from app.schemas.repo_config import RepoReviewConfig

logger = logging.getLogger(__name__)


def parse_repo_review_config(raw_content: str | None) -> RepoReviewConfig | None:
    if not raw_content or not raw_content.strip():
        return None

    try:
        parsed = yaml.safe_load(raw_content)
    except yaml.YAMLError:
        logger.exception("Failed to parse .aireview.yml")
        return None

    if not isinstance(parsed, dict):
        logger.warning(".aireview.yml did not contain a valid object")
        return None

    try:
        config = RepoReviewConfig.model_validate(parsed)
    except ValidationError:
        logger.exception("Invalid .aireview.yml schema")
        return None

    normalized_mode = config.mode.strip().lower()
    if normalized_mode not in {"quick", "security", "maintainability"}:
        logger.warning("Unsupported review mode in .aireview.yml: %s", config.mode)
        config.mode = "quick"
    else:
        config.mode = normalized_mode

    return config


def build_runtime_review_config(
    repo_config: RepoReviewConfig | None,
    *,
    default_mode: str = "quick",
    default_min_inline_comment_confidence: float,
    default_max_inline_comments: int,
    default_summary_max_chunks: int,
) -> dict[str, object]:
    if repo_config is None:
        return {
            "mode": default_mode,
            "min_inline_comment_confidence": default_min_inline_comment_confidence,
            "max_inline_comments": default_max_inline_comments,
            "ignored_paths": [],
            "summary_max_chunks": default_summary_max_chunks,
        }

    return {
        "mode": repo_config.mode or default_mode,
        "min_inline_comment_confidence": (
            repo_config.min_inline_comment_confidence
            if repo_config.min_inline_comment_confidence is not None
            else default_min_inline_comment_confidence
        ),
        "max_inline_comments": (
            repo_config.max_inline_comments
            if repo_config.max_inline_comments is not None
            else default_max_inline_comments
        ),
        "ignored_paths": repo_config.ignored_paths,
        "summary_max_chunks": (
            repo_config.summary_max_chunks
            if repo_config.summary_max_chunks is not None
            else default_summary_max_chunks
        ),
    }
