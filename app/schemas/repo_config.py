from pydantic import BaseModel, Field


class RepoReviewConfig(BaseModel):
    mode: str = Field(default="quick")
    min_inline_comment_confidence: float | None = None
    max_inline_comments: int | None = None
    ignored_paths: list[str] = Field(default_factory=list)
    summary_max_chunks: int | None = None
