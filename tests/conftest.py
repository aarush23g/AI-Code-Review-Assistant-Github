"""Shared test fixtures for the AI Code Review Assistant test suite."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.github.client import GitHubAPIClient
from app.storage.metrics_store import ReviewMetricsStore

# ---------------------------------------------------------------------------
# PR Context fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_pr_context() -> dict[str, Any]:
    """A reusable fake PR context dict used across review service tests."""
    return {
        "pull_request": {
            "number": 14,
            "title": "Add webhook support",
            "body": "Initial PR",
            "state": "open",
            "html_url": "https://github.com/example/repo/pull/14",
            "base_ref": "main",
            "head_ref": "feature/webhook",
            "head_sha": "abc123",
        },
        "files": [{"filename": "app/api/routes/webhook.py"}],
        "reviewable_files": [
            {
                "filename": "app/api/routes/webhook.py",
                "patch": "@@ -1 +1 @@\n-print('old')\n+print('new')\n",
            }
        ],
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
        "runtime_config": {
            "mode": "security",
            "summary_max_chunks": 4,
            "max_inline_comments": 2,
            "min_inline_comment_confidence": 0.9,
            "ignored_paths": [],
        },
    }


# ---------------------------------------------------------------------------
# Webhook payload fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_webhook_payload() -> dict[str, Any]:
    """A reusable fake GitHub webhook payload for PR events."""
    return {
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


# ---------------------------------------------------------------------------
# Mock GitHub client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_github_client() -> GitHubAPIClient:
    """A GitHubAPIClient with all async methods mocked via AsyncMock."""
    client = GitHubAPIClient()
    client.get_pull_request = AsyncMock(
        return_value={
            "number": 14,
            "title": "Add webhook support",
            "body": "Initial PR",
            "state": "open",
            "html_url": "https://github.com/example/repo/pull/14",
            "user": {"login": "aaruush"},
            "base": {"ref": "main"},
            "head": {"ref": "feature/webhook", "sha": "abc123"},
        }
    )
    client.get_pull_request_files = AsyncMock(
        return_value=[
            {
                "filename": "app/main.py",
                "status": "modified",
                "additions": 12,
                "deletions": 2,
                "changes": 14,
                "patch": "@@ -1,2 +1,12 @@\n-print('old')\n+print('new')\n",
                "blob_url": "https://github.com/example/repo/blob/main/app/main.py",
                "raw_url": "https://raw.githubusercontent.com/example/repo/main/app/main.py",
            }
        ]
    )
    client.get_repository_file_content = AsyncMock(return_value=None)
    client.list_issue_comments = AsyncMock(return_value=[])
    client.create_issue_comment = AsyncMock(
        return_value={
            "id": 999,
            "html_url": "https://github.com/example/repo/pull/14#issuecomment-999",
        }
    )
    client.update_issue_comment = AsyncMock(
        return_value={
            "id": 123,
            "html_url": "https://github.com/example/repo/pull/14#issuecomment-123",
        }
    )
    client.create_pull_request_review_comment = AsyncMock(return_value={"id": 777})
    # Mock close to prevent actual HTTP client cleanup in tests
    client.close = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Metrics store fixture (temp directory)
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_metrics_store(tmp_path) -> ReviewMetricsStore:
    """A ReviewMetricsStore backed by a temp SQLite database."""
    return ReviewMetricsStore(str(tmp_path / "test_metrics.sqlite3"))
