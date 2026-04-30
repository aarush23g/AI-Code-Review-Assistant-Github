from app.storage.repository import (
    find_existing_review_comment,
    has_existing_review_comment,
)


def test_has_existing_review_comment_returns_true_when_marker_found() -> None:
    comments = [
        {"body": "Regular comment"},
        {"id": 123, "body": "<!-- ai-code-review-assistant -->\nAI summary here"},
    ]

    assert has_existing_review_comment(comments) is True


def test_has_existing_review_comment_returns_false_when_marker_missing() -> None:
    comments = [
        {"body": "Regular comment"},
        {"body": "Another human review"},
    ]

    assert has_existing_review_comment(comments) is False


def test_find_existing_review_comment_returns_matching_comment() -> None:
    comments = [
        {"body": "Regular comment"},
        {"id": 123, "body": "<!-- ai-code-review-assistant -->\nAI summary here"},
    ]

    result = find_existing_review_comment(comments)

    assert result is not None
    assert result["id"] == 123


def test_find_existing_review_comment_returns_none_when_missing() -> None:
    comments = [{"body": "Regular comment"}]

    result = find_existing_review_comment(comments)

    assert result is None
