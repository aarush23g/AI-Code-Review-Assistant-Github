from app.review.prompt_builder import (
    build_inline_findings_prompt,
    build_pr_summary_review_prompt,
)


def test_build_pr_summary_review_prompt_contains_pr_context() -> None:
    pr_context = {
        "pull_request": {
            "number": 14,
            "title": "Add webhook support",
            "body": "Initial PR",
            "state": "open",
            "base_ref": "main",
            "head_ref": "feature/webhook",
        },
        "review_chunks": [
            {
                "chunk_id": "app/main.py::chunk-1",
                "filename": "app/main.py",
                "chunk_index": 1,
                "total_chunks": 1,
                "patch": "@@ -1 +1 @@\n-print('old')\n+print('new')\n",
                "additions": 1,
                "deletions": 1,
                "changes": 2,
                "status": "modified",
                "blob_url": None,
                "raw_url": None,
            }
        ],
    }

    prompt = build_pr_summary_review_prompt(pr_context, mode="quick")

    assert "Add webhook support" in prompt
    assert "app/main.py" in prompt
    assert "summary" in prompt
    assert "top_issues" in prompt


def test_build_pr_summary_review_prompt_contains_security_mode_instruction() -> None:
    pr_context = {
        "pull_request": {
            "number": 14,
            "title": "Harden auth flow",
            "body": "Security changes",
            "state": "open",
            "base_ref": "main",
            "head_ref": "security/auth",
        },
        "review_chunks": [],
    }

    prompt = build_pr_summary_review_prompt(pr_context, mode="security")

    assert "security" in prompt.lower()
    assert "injection" in prompt.lower()


def test_build_inline_findings_prompt_contains_chunk_context() -> None:
    chunk = {
        "chunk_id": "app/main.py::chunk-1",
        "filename": "app/main.py",
        "chunk_index": 1,
        "total_chunks": 1,
        "patch": "@@ -1 +1 @@\n-print('old')\n+print('new')\n",
        "additions": 1,
        "deletions": 1,
        "changes": 2,
        "status": "modified",
        "blob_url": None,
        "raw_url": None,
    }

    prompt = build_inline_findings_prompt(chunk, mode="maintainability")

    assert "app/main.py" in prompt
    assert "findings" in prompt
    assert "line" in prompt
    assert "maintainability" in prompt.lower()
