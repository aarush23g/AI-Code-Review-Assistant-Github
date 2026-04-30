from app.review.diff_parser import filter_reviewable_files
from app.schemas.github import PullRequestFile


def test_filter_reviewable_files_skips_ignored_and_empty_patch() -> None:
    files = [
        PullRequestFile(
            filename="package-lock.json",
            status="modified",
            additions=10,
            deletions=2,
            changes=12,
            patch="some patch",
        ),
        PullRequestFile(
            filename="app/main.py",
            status="modified",
            additions=5,
            deletions=1,
            changes=6,
            patch="@@ -1 +1 @@\n-print('old')\n+print('new')\n",
        ),
        PullRequestFile(
            filename="docs/readme.md",
            status="modified",
            additions=3,
            deletions=0,
            changes=3,
            patch=None,
        ),
    ]

    result = filter_reviewable_files(files)

    assert len(result) == 1
    assert result[0].filename == "app/main.py"


def test_filter_reviewable_files_respects_custom_ignored_paths() -> None:
    files = [
        PullRequestFile(
            filename="docs/guide.md",
            status="modified",
            additions=5,
            deletions=1,
            changes=6,
            patch="@@ -1 +1 @@\n-old\n+new\n",
        ),
        PullRequestFile(
            filename="app/main.py",
            status="modified",
            additions=5,
            deletions=1,
            changes=6,
            patch="@@ -1 +1 @@\n-print('old')\n+print('new')\n",
        ),
    ]

    result = filter_reviewable_files(files, ignored_paths=["docs/"])

    assert len(result) == 1
    assert result[0].filename == "app/main.py"
