from __future__ import annotations

from app.review.rules import is_patch_reviewable, should_ignore_file
from app.schemas.github import PullRequestFile
from app.schemas.review import ReviewableFile


def _matches_custom_ignored_path(filename: str, ignored_paths: list[str]) -> bool:
    normalized_filename = filename.replace("\\", "/").lower()

    for path in ignored_paths:
        normalized_path = path.replace("\\", "/").strip().lower()
        if not normalized_path:
            continue
        if normalized_filename.startswith(normalized_path):
            return True

    return False


def filter_reviewable_files(
    files: list[PullRequestFile],
    max_patch_chars: int = 12000,
    ignored_paths: list[str] | None = None,
) -> list[ReviewableFile]:
    reviewable_files: list[ReviewableFile] = []
    ignored_paths = ignored_paths or []

    for file in files:
        if should_ignore_file(file.filename):
            continue

        if _matches_custom_ignored_path(file.filename, ignored_paths):
            continue

        if not is_patch_reviewable(file.patch, max_patch_chars=max_patch_chars):
            continue

        reviewable_files.append(
            ReviewableFile(
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=file.patch or "",
                blob_url=file.blob_url,
                raw_url=file.raw_url,
            )
        )

    return reviewable_files
