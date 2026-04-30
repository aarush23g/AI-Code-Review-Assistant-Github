import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def build_signature(payload: bytes, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def test_github_webhook_accepts_supported_pr_action() -> None:
    secret = get_settings().github_webhook_secret

    payload = {
        "action": "opened",
        "pull_request": {
            "number": 14,
            "title": "Add webhook support",
            "body": "Initial PR",
            "state": "open",
            "html_url": "https://github.com/example/repo/pull/14",
            "diff_url": "https://github.com/example/repo/pull/14.diff",
            "patch_url": "https://github.com/example/repo/pull/14.patch",
            "head": {"ref": "feature/webhook"},
            "base": {"ref": "main"},
            "user": {"login": "aaruush"},
        },
        "repository": {
            "full_name": "example/repo",
            "private": False,
            "html_url": "https://github.com/example/repo",
        },
        "installation": {"id": 12345},
        "sender": {"login": "aaruush"},
    }

    raw_body = json.dumps(payload).encode("utf-8")
    signature = build_signature(raw_body, secret)

    with (
        patch(
            "app.api.routes.webhook.ReviewService.fetch_pull_request_context",
            new=AsyncMock(
                return_value={
                    "pull_request": {
                        "number": 14,
                        "title": "Add webhook support",
                        "state": "open",
                        "html_url": "https://github.com/example/repo/pull/14",
                        "base_ref": "main",
                        "head_ref": "feature/webhook",
                        "head_sha": "abc123",
                    },
                    "files": [],
                    "reviewable_files": [{"filename": "app/api/routes/webhook.py"}],
                    "review_chunks": [
                        {
                            "chunk_id": "app/api/routes/webhook.py::chunk-1",
                            "filename": "app/api/routes/webhook.py",
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
            ),
        ),
        patch(
            "app.api.routes.webhook.ReviewService.generate_pr_summary_review",
            new=AsyncMock(
                return_value={
                    "status": "completed",
                    "reason": "normal",
                    "strategy": "full_summary",
                    "review": {
                        "summary": "This PR adds webhook support.",
                        "top_issues": [],
                        "risky_files": [],
                        "suggested_tests": [],
                    },
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150,
                    },
                    "model": "gpt-4.1-mini",
                }
            ),
        ),
        patch(
            "app.api.routes.webhook.ReviewService.publish_pr_summary_review",
            new=AsyncMock(
                return_value={
                    "status": "posted",
                    "comment_id": 999,
                    "html_url": "https://github.com/example/repo/pull/14#issuecomment-999",
                }
            ),
        ),
        patch(
            "app.api.routes.webhook.ReviewService.generate_inline_review_findings",
            new=AsyncMock(
                return_value=[
                    {
                        "severity": "high",
                        "title": "Missing validation",
                        "explanation": "Input is not validated.",
                        "filename": "app/api/routes/webhook.py",
                        "line": 12,
                        "confidence": 0.95,
                    }
                ]
            ),
        ),
        patch(
            "app.api.routes.webhook.ReviewService.publish_inline_review_comments",
            new=AsyncMock(return_value=[{"status": "posted", "comment_id": 777}]),
        ),
    ):
        response = client.post(
            "/webhooks/github",
            content=raw_body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["action"] == "opened"
    assert response.json()["pr_number"] == 14


def test_github_webhook_skips_publish_when_review_is_skipped() -> None:
    secret = get_settings().github_webhook_secret

    payload = {
        "action": "opened",
        "pull_request": {
            "number": 22,
            "title": "Update lockfiles",
            "body": "Dependency refresh",
            "state": "open",
            "html_url": "https://github.com/example/repo/pull/22",
            "diff_url": "https://github.com/example/repo/pull/22.diff",
            "patch_url": "https://github.com/example/repo/pull/22.patch",
            "head": {"ref": "deps/update"},
            "base": {"ref": "main"},
            "user": {"login": "aaruush"},
        },
        "repository": {
            "full_name": "example/repo",
            "private": False,
            "html_url": "https://github.com/example/repo",
        },
        "installation": {"id": 12345},
        "sender": {"login": "aaruush"},
    }

    raw_body = json.dumps(payload).encode("utf-8")
    signature = build_signature(raw_body, secret)

    with (
        patch(
            "app.api.routes.webhook.ReviewService.fetch_pull_request_context",
            new=AsyncMock(
                return_value={
                    "pull_request": {
                        "number": 22,
                        "title": "Update lockfiles",
                        "state": "open",
                        "html_url": "https://github.com/example/repo/pull/22",
                        "base_ref": "main",
                        "head_ref": "deps/update",
                    },
                    "files": [{"filename": "package-lock.json"}],
                    "reviewable_files": [],
                    "review_chunks": [],
                }
            ),
        ),
        patch(
            "app.api.routes.webhook.ReviewService.generate_pr_summary_review",
            new=AsyncMock(
                return_value={
                    "status": "skipped",
                    "reason": "no_reviewable_files",
                    "strategy": "skip",
                    "review": None,
                    "usage": None,
                    "model": None,
                }
            ),
        ),
        patch(
            "app.api.routes.webhook.ReviewService.publish_pr_summary_review",
            new=AsyncMock(),
        ) as mocked_publish,
    ):
        response = client.post(
            "/webhooks/github",
            content=raw_body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert "review skipped" in response.json()["message"]
    mocked_publish.assert_not_called()


def test_github_webhook_rejects_invalid_signature() -> None:
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 14,
            "title": "Add webhook support",
        },
        "repository": {
            "full_name": "example/repo",
        },
    }

    raw_body = json.dumps(payload).encode("utf-8")

    response = client.post(
        "/webhooks/github",
        content=raw_body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=bad",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature"


def test_github_webhook_ignores_unsupported_pr_action() -> None:
    secret = get_settings().github_webhook_secret

    payload = {
        "action": "closed",
        "pull_request": {
            "number": 14,
            "title": "Add webhook support",
            "body": "Initial PR",
            "state": "closed",
            "html_url": "https://github.com/example/repo/pull/14",
            "diff_url": "https://github.com/example/repo/pull/14.diff",
            "patch_url": "https://github.com/example/repo/pull/14.patch",
            "head": {"ref": "feature/webhook"},
            "base": {"ref": "main"},
            "user": {"login": "aaruush"},
        },
        "repository": {
            "full_name": "example/repo",
            "private": False,
            "html_url": "https://github.com/example/repo",
        },
        "installation": {"id": 12345},
        "sender": {"login": "aaruush"},
    }

    raw_body = json.dumps(payload).encode("utf-8")
    signature = build_signature(raw_body, secret)

    response = client.post(
        "/webhooks/github",
        content=raw_body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["action"] == "closed"
