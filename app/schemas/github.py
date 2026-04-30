from pydantic import BaseModel


class PullRequestFile(BaseModel):
    filename: str
    status: str
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: str | None = None
    blob_url: str | None = None
    raw_url: str | None = None


class PullRequestDetails(BaseModel):
    number: int
    title: str
    body: str | None = None
    state: str
    html_url: str
    user_login: str | None = None
    base_ref: str | None = None
    head_ref: str | None = None
    head_sha: str | None = None
