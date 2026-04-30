from __future__ import annotations

from pathlib import PurePosixPath

IGNORED_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
}

IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".exe",
    ".dll",
    ".so",
    ".bin",
    ".mp4",
    ".mp3",
    ".wav",
    ".jar",
    ".class",
    ".min.js",
    ".min.css",
}

IGNORED_PATH_PARTS = {
    "node_modules",
    ".next",
    "dist",
    "build",
    "coverage",
    ".git",
    "vendor",
    "venv",
    ".venv",
    "__pycache__",
    "migrations",
}


def should_ignore_file(filename: str) -> bool:
    path = PurePosixPath(filename)

    if path.name in IGNORED_FILENAMES:
        return True

    path_str = filename.lower()

    for ignored in IGNORED_EXTENSIONS:
        if path_str.endswith(ignored):
            return True

    for part in path.parts:
        if part.lower() in IGNORED_PATH_PARTS:
            return True

    return False


def is_patch_reviewable(patch: str | None, max_patch_chars: int = 12000) -> bool:
    if patch is None:
        return False

    stripped = patch.strip()

    if not stripped:
        return False

    if len(stripped) > max_patch_chars:
        return False

    return True
