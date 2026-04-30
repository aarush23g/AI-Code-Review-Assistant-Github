from __future__ import annotations

from typing import Any

REVIEW_BOT_MARKER = "<!-- ai-code-review-assistant -->"


def format_pr_summary_comment(
    review: dict[str, Any],
    repository_full_name: str,
    pull_number: int,
) -> str:
    summary = review.get("summary", "").strip()
    top_issues = review.get("top_issues", [])
    risky_files = review.get("risky_files", [])
    suggested_tests = review.get("suggested_tests", [])

    lines: list[str] = [
        REVIEW_BOT_MARKER,
        "## AI Code Review Summary",
        "",
        f"Repository: `{repository_full_name}`  ",
        f"Pull Request: `#{pull_number}`",
        "",
        "### Overview",
        summary or "No meaningful issues were identified in the reviewed diff chunks.",
        "",
    ]

    if top_issues:
        lines.extend(["### Top Issues", ""])
        for idx, issue in enumerate(top_issues, start=1):
            severity = str(issue.get("severity", "medium")).upper()
            title = str(issue.get("title", "Untitled issue")).strip()
            explanation = str(issue.get("explanation", "")).strip()
            filename = issue.get("filename")
            confidence = issue.get("confidence", 0.0)

            line = f"{idx}. **[{severity}] {title}**"
            if filename:
                line += f" — `{filename}`"
            line += f" (confidence: {confidence:.2f})"

            lines.append(line)

            if explanation:
                lines.append(f"   - {explanation}")

        lines.append("")
    else:
        lines.extend(
            [
                "### Top Issues",
                "",
                "No high-signal issues were identified.",
                "",
            ]
        )

    if risky_files:
        lines.extend(["### Risky Files", ""])
        for file in risky_files:
            lines.append(f"- `{file}`")
        lines.append("")

    if suggested_tests:
        lines.extend(["### Suggested Follow-up Tests", ""])
        for test in suggested_tests:
            lines.append(f"- {test}")
        lines.append("")

    lines.extend(
        [
            "---",
            "_This is an automated first-pass review. Please verify findings before acting on them._",
        ]
    )

    return "\n".join(lines)
