from __future__ import annotations

from app.github.comments import REVIEW_BOT_MARKER


def has_existing_review_comment(comments: list[dict]) -> bool:
    return find_existing_review_comment(comments) is not None


def find_existing_review_comment(comments: list[dict]) -> dict | None:
    for comment in comments:
        body = comment.get("body", "")
        if REVIEW_BOT_MARKER in body:
            return comment
    return None
