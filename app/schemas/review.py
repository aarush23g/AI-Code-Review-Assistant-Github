from pydantic import BaseModel, Field


class ReviewableFile(BaseModel):
    filename: str
    status: str
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: str
    blob_url: str | None = None
    raw_url: str | None = None


class ReviewChunk(BaseModel):
    chunk_id: str = Field(...)
    filename: str = Field(...)
    chunk_index: int = Field(...)
    total_chunks: int = Field(...)
    patch: str = Field(...)
    additions: int = Field(default=0)
    deletions: int = Field(default=0)
    changes: int = Field(default=0)
    status: str = Field(...)
    blob_url: str | None = None
    raw_url: str | None = None


class TopIssue(BaseModel):
    severity: str
    title: str
    explanation: str
    filename: str | None = None
    confidence: float


class PRSummaryReview(BaseModel):
    summary: str
    top_issues: list[TopIssue]
    risky_files: list[str]
    suggested_tests: list[str]


class InlineReviewFinding(BaseModel):
    severity: str
    title: str
    explanation: str
    filename: str
    line: int
    confidence: float


class InlineReviewResult(BaseModel):
    findings: list[InlineReviewFinding]


class ReviewExecutionResult(BaseModel):
    status: str
    reason: str
    strategy: str
    review: dict | None = None
    usage: dict | None = None
    model: str | None = None
