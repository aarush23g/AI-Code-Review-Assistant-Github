import logging
from time import perf_counter

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.core.security import verify_github_signature
from app.schemas.webhook import PullRequestWebhookPayload, WebhookAckResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

logger = logging.getLogger(__name__)

SUPPORTED_PR_ACTIONS = {"opened", "reopened", "synchronize"}


@router.post("/github", response_model=WebhookAckResponse)
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> WebhookAckResponse:
    settings = get_settings()
    raw_body = await request.body()

    if not verify_github_signature(
        payload=raw_body,
        signature_header=x_hub_signature_256,
        secret=settings.github_webhook_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    if x_github_event != "pull_request":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported GitHub event. Only pull_request is handled.",
        )

    try:
        payload = PullRequestWebhookPayload.model_validate_json(raw_body)
    except Exception as exc:
        logger.exception("Failed to parse webhook payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        ) from exc

    if payload.action not in SUPPORTED_PR_ACTIONS:
        return WebhookAckResponse(
            status="ignored",
            event=x_github_event,
            action=payload.action,
            repository=payload.repository.full_name,
            pr_number=payload.pull_request.number,
            message="PR action ignored",
        )

    if payload.installation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing installation information in webhook payload",
        )

    review_service = ReviewService()
    review_start = perf_counter()

    try:
        pr_context = await review_service.fetch_pull_request_context(
            repository_full_name=payload.repository.full_name,
            pull_number=payload.pull_request.number,
            installation_id=payload.installation.id,
        )
    except Exception as exc:
        logger.exception("Failed to fetch PR context from GitHub")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch pull request context from GitHub",
        ) from exc

    try:
        review_result = await review_service.generate_pr_summary_review(pr_context)
    except Exception as exc:
        logger.exception("Failed to generate AI review")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate AI pull request review",
        ) from exc

    if review_result["status"] == "skipped":
        logger.info(
            "Skipping PR review publish | repo=%s pr=%s reason=%s",
            payload.repository.full_name,
            payload.pull_request.number,
            review_result["reason"],
        )

        duration_ms = round((perf_counter() - review_start) * 1000, 2)
        review_service.record_review_metrics(
            repository_full_name=payload.repository.full_name,
            pull_number=payload.pull_request.number,
            pr_context=pr_context,
            review_result=review_result,
            inline_findings=[],
            inline_publish_results=[],
            duration_ms=duration_ms,
        )

        skipped_reason = review_result["reason"]
        skipped_message = (
            "Pull request webhook accepted; " f"review skipped ({skipped_reason})"
        )

        return WebhookAckResponse(
            status="accepted",
            event=x_github_event,
            action=payload.action,
            repository=payload.repository.full_name,
            pr_number=payload.pull_request.number,
            message=skipped_message,
        )

    try:
        publish_result = await review_service.publish_pr_summary_review(
            repository_full_name=payload.repository.full_name,
            pull_number=payload.pull_request.number,
            installation_id=payload.installation.id,
            review=review_result["review"],
        )
        logger.info(
            "PR summary publish result | repo=%s pr=%s status=%s strategy=%s",
            payload.repository.full_name,
            payload.pull_request.number,
            publish_result["status"],
            review_result["strategy"],
        )
    except Exception as exc:
        logger.exception("Failed to publish review comment to GitHub")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to publish AI review comment to GitHub",
        ) from exc

    try:
        inline_findings = await review_service.generate_inline_review_findings(
            pr_context
        )
        commit_id = (
            pr_context["pull_request"].get("head_sha") or payload.pull_request.number
        )
        inline_publish_results = await review_service.publish_inline_review_comments(
            repository_full_name=payload.repository.full_name,
            pull_number=payload.pull_request.number,
            installation_id=payload.installation.id,
            commit_id=str(commit_id),
            findings=inline_findings,
        )

        duration_ms = round((perf_counter() - review_start) * 1000, 2)
        review_service.record_review_metrics(
            repository_full_name=payload.repository.full_name,
            pull_number=payload.pull_request.number,
            pr_context=pr_context,
            review_result=review_result,
            inline_findings=inline_findings,
            inline_publish_results=inline_publish_results,
            duration_ms=duration_ms,
        )
    except Exception:
        logger.exception("Failed during inline review generation/publishing")

    return WebhookAckResponse(
        status="accepted",
        event=x_github_event,
        action=payload.action,
        repository=payload.repository.full_name,
        pr_number=payload.pull_request.number,
        message="Pull request webhook accepted and review processed",
    )
