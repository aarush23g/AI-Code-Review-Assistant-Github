from app.review.line_mapper import (
    build_changed_line_map,
    extract_added_lines_from_patch,
    is_valid_inline_finding_line,
)


def test_extract_added_lines_from_single_hunk() -> None:
    patch = "@@ -10,2 +10,3 @@\n" " old_line\n" "+new_line\n" " unchanged_line\n"

    result = extract_added_lines_from_patch(patch)

    assert result == {11}


def test_extract_added_lines_from_multiple_hunks() -> None:
    patch = (
        "@@ -1,2 +1,3 @@\n"
        " line_one\n"
        "+added_one\n"
        " line_two\n"
        "@@ -20,2 +21,3 @@\n"
        " line_twenty\n"
        "+added_two\n"
        " line_twenty_two\n"
    )

    result = extract_added_lines_from_patch(patch)

    assert result == {2, 22}


def test_extract_added_lines_ignores_removed_lines() -> None:
    patch = "@@ -5,3 +5,3 @@\n" "-removed_line\n" "+added_line\n" " unchanged_line\n"

    result = extract_added_lines_from_patch(patch)

    assert result == {5}


def test_build_changed_line_map() -> None:
    reviewable_files = [
        {
            "filename": "app/main.py",
            "patch": "@@ -1,1 +1,2 @@\n+new_line\n",
        }
    ]

    result = build_changed_line_map(reviewable_files)

    assert result == {"app/main.py": {1}}


def test_is_valid_inline_finding_line() -> None:
    changed_line_map = {
        "app/main.py": {10, 11, 12},
    }

    assert is_valid_inline_finding_line("app/main.py", 11, changed_line_map) is True
    assert is_valid_inline_finding_line("app/main.py", 99, changed_line_map) is False
