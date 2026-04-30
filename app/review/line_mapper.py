from __future__ import annotations

import re
from dataclasses import dataclass

HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass(frozen=True)
class FileChangedLines:
    filename: str
    changed_lines: set[int]


def extract_added_lines_from_patch(patch: str) -> set[int]:
    """
    Extract target-side line numbers for added/changed lines from a unified diff patch.

    Only lines beginning with '+' are treated as changed target lines.
    Diff metadata lines like '+++' are ignored.
    """
    changed_lines: set[int] = set()
    current_new_line: int | None = None

    for raw_line in patch.splitlines():
        hunk_match = HUNK_HEADER_RE.match(raw_line)

        if hunk_match:
            current_new_line = int(hunk_match.group("new_start"))
            continue

        if current_new_line is None:
            continue

        if raw_line.startswith("+++"):
            continue

        if raw_line.startswith("+"):
            changed_lines.add(current_new_line)
            current_new_line += 1
            continue

        if raw_line.startswith("-"):
            continue

        current_new_line += 1

    return changed_lines


def build_changed_line_map(reviewable_files: list[dict]) -> dict[str, set[int]]:
    line_map: dict[str, set[int]] = {}

    for file in reviewable_files:
        filename = file["filename"]
        patch = file.get("patch") or ""
        line_map[filename] = extract_added_lines_from_patch(patch)

    return line_map


def is_valid_inline_finding_line(
    filename: str,
    line: int,
    changed_line_map: dict[str, set[int]],
) -> bool:
    return line in changed_line_map.get(filename, set())
