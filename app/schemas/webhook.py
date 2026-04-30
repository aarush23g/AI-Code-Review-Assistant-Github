from typing import Any

from pydantic import BaseModel, Field


class PullRequestBranch(BaseModel):
    ref: str | None = None


class PullRequestUser(BaseModel):
    login: str | None = None


class PullRequestInfo(BaseModel):
    number: int
    title: str | None = None
    body: str | None = None
    state: str | None = None
    html_url: str | None = None
    diff_url: str | None = None
    patch_url: str | None = None
    head: PullRequestBranch | None = None
    base: PullRequestBranch | None = None
    user: PullRequestUser | None = None


class RepositoryInfo(BaseModel):
    full_name: str
    private: bool | None = None
    html_url: str | None = None


class InstallationInfo(BaseModel):
    id: int


class PullRequestWebhookPayload(BaseModel):
    action: str
    pull_request: PullRequestInfo
    repository: RepositoryInfo
    installation: InstallationInfo | None = None
    sender: PullRequestUser | None = None
    extra: dict[str, Any] | None = None


class WebhookAckResponse(BaseModel):
    status: str = Field(...)
    event: str = Field(...)
    action: str = Field(...)
    repository: str = Field(...)
    pr_number: int = Field(...)
    message: str = Field(...)
