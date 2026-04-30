from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.schemas.review import InlineReviewResult, PRSummaryReview


class LLMReviewer:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_pr_summary_review(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")

        parsed: dict[str, Any] = json.loads(content)
        validated_review = PRSummaryReview.model_validate(parsed)

        usage = getattr(response, "usage", None)
        usage_data = None
        if usage is not None:
            usage_data = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        return {
            "review": validated_review,
            "usage": usage_data,
            "model": self.model,
        }

    async def generate_inline_findings(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty inline findings content")

        parsed: dict[str, Any] = json.loads(content)
        validated = InlineReviewResult.model_validate(parsed)

        usage = getattr(response, "usage", None)
        usage_data = None
        if usage is not None:
            usage_data = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        return {
            "result": validated,
            "usage": usage_data,
            "model": self.model,
        }
