from app.github.comments import REVIEW_BOT_MARKER, format_pr_summary_comment


def test_format_pr_summary_comment_contains_sections() -> None:
    review = {
        "summary": "This PR adds webhook validation.",
        "top_issues": [
            {
                "severity": "high",
                "title": "Missing edge-case validation",
                "explanation": "Malformed signature headers are not fully covered.",
                "filename": "app/api/routes/webhook.py",
                "confidence": 0.91,
            }
        ],
        "risky_files": ["app/api/routes/webhook.py"],
        "suggested_tests": ["Add a malformed signature header test."],
    }

    body = format_pr_summary_comment(
        review=review,
        repository_full_name="example/repo",
        pull_number=14,
    )

    assert REVIEW_BOT_MARKER in body
    assert "## AI Code Review Summary" in body
    assert "### Top Issues" in body
    assert "### Risky Files" in body
    assert "### Suggested Follow-up Tests" in body
    assert "app/api/routes/webhook.py" in body
