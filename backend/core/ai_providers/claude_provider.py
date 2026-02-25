import json
import logging
from typing import Optional

import anthropic
from django.conf import settings

from .base import AnalysisContext, BaseAIProvider, RecommendationData

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseAIProvider):
    """AI analysis via Anthropic Claude (claude-sonnet-4-6)."""

    provider_name = "claude"
    MODEL = "claude-sonnet-4-6"

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def analyze(self, context: AnalysisContext) -> RecommendationData:
        prompt = self.build_prompt(context)
        logger.info("Running Claude analysis for %s", context.symbol)

        message = self._client.messages.create(
            model=self.MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_response = message.content[0].text
        return self._parse_response(raw_response, context)

    def _parse_response(self, raw: str, context: AnalysisContext) -> RecommendationData:
        try:
            # Strip markdown code blocks if present
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return RecommendationData(
                action=data.get("action", "HOLD"),
                confidence=float(data.get("confidence", 0.5)),
                quantity_suggested=float(data.get("quantity_suggested", 0)),
                price_target=data.get("price_target"),
                stop_loss=data.get("stop_loss"),
                take_profit=data.get("take_profit"),
                reasoning=data.get("reasoning", ""),
                raw_response=raw,
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Claude response parse error: %s\nRaw: %s", exc, raw)
            return RecommendationData(
                action="HOLD",
                confidence=0.0,
                quantity_suggested=0,
                price_target=None,
                stop_loss=None,
                take_profit=None,
                reasoning=f"Failed to parse AI response: {exc}",
                raw_response=raw,
            )
