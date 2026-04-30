from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are a senior software engineer performing a first-pass code review on a GitHub pull request.

Your job is to identify likely bugs, correctness risks, maintainability concerns, and notable testing gaps.

Rules:
- Review only the provided pull request context and changed code.
- Focus on high-signal issues only.
- Do not nitpick minor style issues.
- Do not invent problems without evidence.
- If there are no meaningful issues, say so clearly.
- Be concise but specific.
- Return valid JSON only.
"""


INLINE_FINDINGS_SYSTEM_PROMPT = """You are a senior software engineer extracting high-confidence inline review findings from a changed code patch.

Rules:
- Only report issues with strong evidence in the provided patch.
- Prefer correctness, bug risk, validation gaps, and maintainability issues.
- Do not report style-only issues.
- Do not invent filenames or line numbers.
- Use the provided filename.
- Use a best-effort changed-line number from the patch hunk.
- If no strong issue exists, return an empty findings list.
- Return valid JSON only.
"""


def _mode_instructions(mode: str) -> str:
    normalized = mode.strip().lower()

    if normalized == "security":
        return (
            "Prioritize security issues such as input validation gaps, auth mistakes, "
            "secrets exposure, unsafe deserialization, injection risks, and trust-boundary violations."
        )
    if normalized == "maintainability":
        return (
            "Prioritize maintainability concerns such as fragile logic, poor separation of concerns, "
            "missing error handling, duplication, and testability risks."
        )
    return "Perform a quick high-signal review focused on correctness, risky changes, and important testing gaps."


def build_pr_summary_review_prompt(
    pr_context: dict[str, Any],
    max_chunks: int = 8,
    mode: str = "quick",
) -> str:
    pull_request = pr_context["pull_request"]
    review_chunks = pr_context["review_chunks"][:max_chunks]

    prompt_payload = {
        "review_mode": mode,
        "pull_request": {
            "number": pull_request["number"],
            "title": pull_request["title"],
            "body": pull_request.get("body"),
            "state": pull_request["state"],
            "base_ref": pull_request.get("base_ref"),
            "head_ref": pull_request.get("head_ref"),
        },
        "review_scope": {
            "selected_chunk_count": len(review_chunks),
            "total_available_chunks": len(pr_context["review_chunks"]),
        },
        "review_chunks": review_chunks,
        "output_schema": {
            "summary": "string",
            "top_issues": [
                {
                    "severity": "low|medium|high",
                    "title": "string",
                    "explanation": "string",
                    "filename": "string|null",
                    "confidence": "float between 0 and 1",
                }
            ],
            "risky_files": ["string"],
            "suggested_tests": ["string"],
        },
    }

    instructions = f"""
Review this pull request and return a JSON object with:
- summary
- top_issues
- risky_files
- suggested_tests

Review mode instructions:
{_mode_instructions(mode)}

If there are no meaningful issues:
- make top_issues an empty list
- keep summary honest and concise

Return JSON only. No markdown fences. No prose outside JSON.
"""

    return f"{instructions}\n\nINPUT:\n{json.dumps(prompt_payload, indent=2)}"


def build_inline_findings_prompt(
    review_chunk: dict[str, Any],
    mode: str = "quick",
) -> str:
    prompt_payload = {
        "review_mode": mode,
        "review_chunk": review_chunk,
        "output_schema": {
            "findings": [
                {
                    "severity": "low|medium|high",
                    "title": "string",
                    "explanation": "string",
                    "filename": "string",
                    "line": "integer line number in the changed file",
                    "confidence": "float between 0 and 1",
                }
            ]
        },
    }

    instructions = f"""
Review this changed code chunk and return JSON with:
- findings

Review mode instructions:
{_mode_instructions(mode)}

Only include findings that are strong enough to justify an inline review comment.
If there are no strong findings, return:
{{"findings": []}}

Return JSON only. No markdown fences. No prose outside JSON.
"""

    return f"{instructions}\n\nINPUT:\n{json.dumps(prompt_payload, indent=2)}"
