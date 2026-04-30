from app.review.post_processor import (
    normalize_inline_review_result,
    select_inline_findings,
)
from app.schemas.review import InlineReviewFinding, InlineReviewResult


def test_normalize_inline_review_result_clamps_and_normalizes() -> None:
    result = InlineReviewResult(
        findings=[
            InlineReviewFinding(
                severity="HIGH",
                title="  Missing validation  ",
                explanation="  Input is not validated.  ",
                filename=" app/main.py ",
                line=0,
                confidence=1.5,
            )
        ]
    )

    normalized = normalize_inline_review_result(result)

    assert normalized.findings[0].severity == "high"
    assert normalized.findings[0].title == "Missing validation"
    assert normalized.findings[0].explanation == "Input is not validated."
    assert normalized.findings[0].filename == "app/main.py"
    assert normalized.findings[0].line == 1
    assert normalized.findings[0].confidence == 1.0


def test_select_inline_findings_filters_and_limits() -> None:
    result = InlineReviewResult(
        findings=[
            InlineReviewFinding(
                severity="high",
                title="Missing validation",
                explanation="Input is not validated.",
                filename="app/main.py",
                line=10,
                confidence=0.95,
            ),
            InlineReviewFinding(
                severity="low",
                title="Minor naming concern",
                explanation="Variable name could be clearer.",
                filename="app/main.py",
                line=12,
                confidence=0.40,
            ),
        ]
    )

    selected = select_inline_findings(result, {"app/main.py"})

    assert len(selected) == 1
    assert selected[0].title == "Missing validation"


def test_select_inline_findings_filters_invalid_changed_lines() -> None:
    result = InlineReviewResult(
        findings=[
            InlineReviewFinding(
                severity="high",
                title="Valid changed line issue",
                explanation="This targets a real changed line.",
                filename="app/main.py",
                line=11,
                confidence=0.95,
            ),
            InlineReviewFinding(
                severity="high",
                title="Invalid unchanged line issue",
                explanation="This targets a line not in the diff.",
                filename="app/main.py",
                line=20,
                confidence=0.95,
            ),
        ]
    )

    selected = select_inline_findings(
        result,
        {"app/main.py"},
        changed_line_map={"app/main.py": {11}},
    )

    assert len(selected) == 1
    assert selected[0].title == "Valid changed line issue"


def test_select_inline_findings_dedupes_same_file_line_title() -> None:
    result = InlineReviewResult(
        findings=[
            InlineReviewFinding(
                severity="high",
                title="Missing validation",
                explanation="First version.",
                filename="app/main.py",
                line=11,
                confidence=0.95,
            ),
            InlineReviewFinding(
                severity="high",
                title="Missing validation",
                explanation="Duplicate version.",
                filename="app/main.py",
                line=11,
                confidence=0.96,
            ),
        ]
    )

    selected = select_inline_findings(
        result,
        {"app/main.py"},
        changed_line_map={"app/main.py": {11}},
    )

    assert len(selected) == 1
