from __future__ import annotations

from app.core.config import get_settings
from app.schemas.review import (
    InlineReviewFinding,
    InlineReviewResult,
    PRSummaryReview,
    TopIssue,
)


def normalize_pr_summary_review(review: PRSummaryReview) -> PRSummaryReview:
    normalized_issues: list[TopIssue] = []

    for issue in review.top_issues:
        confidence = max(0.0, min(1.0, issue.confidence))
        severity = issue.severity.lower().strip()

        if severity not in {"low", "medium", "high"}:
            severity = "medium"

        normalized_issues.append(
            TopIssue(
                severity=severity,
                title=issue.title.strip(),
                explanation=issue.explanation.strip(),
                filename=issue.filename.strip() if issue.filename else None,
                confidence=confidence,
            )
        )

    unique_risky_files = list(
        dict.fromkeys(file.strip() for file in review.risky_files if file.strip())
    )
    unique_suggested_tests = list(
        dict.fromkeys(test.strip() for test in review.suggested_tests if test.strip())
    )

    return PRSummaryReview(
        summary=review.summary.strip(),
        top_issues=normalized_issues,
        risky_files=unique_risky_files,
        suggested_tests=unique_suggested_tests,
    )


def normalize_inline_review_result(result: InlineReviewResult) -> InlineReviewResult:
    normalized_findings: list[InlineReviewFinding] = []

    for finding in result.findings:
        confidence = max(0.0, min(1.0, finding.confidence))
        severity = finding.severity.lower().strip()

        if severity not in {"low", "medium", "high"}:
            severity = "medium"

        normalized_findings.append(
            InlineReviewFinding(
                severity=severity,
                title=finding.title.strip(),
                explanation=finding.explanation.strip(),
                filename=finding.filename.strip(),
                line=max(1, int(finding.line)),
                confidence=confidence,
            )
        )

    return InlineReviewResult(findings=normalized_findings)


def select_inline_findings(
    result: InlineReviewResult,
    valid_filenames: set[str],
    *,
    min_confidence: float | None = None,
    max_findings: int | None = None,
    changed_line_map: dict[str, set[int]] | None = None,
) -> list[InlineReviewFinding]:
    settings = get_settings()

    confidence_threshold = (
        min_confidence
        if min_confidence is not None
        else settings.min_inline_comment_confidence
    )
    findings_limit = (
        max_findings if max_findings is not None else settings.max_inline_comments
    )

    filtered = []

    for finding in result.findings:
        if finding.filename not in valid_filenames:
            continue

        if finding.confidence < confidence_threshold:
            continue

        if finding.line < 1:
            continue

        if changed_line_map is not None:
            valid_lines = changed_line_map.get(finding.filename, set())
            if finding.line not in valid_lines:
                continue

        filtered.append(finding)

    filtered.sort(
        key=lambda item: (
            {"high": 3, "medium": 2, "low": 1}.get(item.severity, 0),
            item.confidence,
        ),
        reverse=True,
    )

    deduped: list[InlineReviewFinding] = []
    seen = set()

    for finding in filtered:
        key = (
            finding.filename,
            finding.line,
            finding.title.strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)

    return deduped[:findings_limit]
