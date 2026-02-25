import json
import logging

from django.conf import settings

from .base import AnalysisContext, BaseAIProvider, RecommendationData

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """AI analysis via OpenAI GPT-4o."""

    provider_name = "openai"
    MODEL = "gpt-4o"

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def analyze(self, context: AnalysisContext) -> RecommendationData:
        prompt = self.build_prompt(context)
        logger.info("Running OpenAI analysis for %s", context.symbol)

        response = self._client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert stock analyst. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=512,
            response_format={"type": "json_object"},
        )

        raw_response = response.choices[0].message.content
        return self._parse_response(raw_response, context)

    def _parse_response(self, raw: str, context: AnalysisContext) -> RecommendationData:
        try:
            data = json.loads(raw)
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
            logger.error("OpenAI response parse error: %s\nRaw: %s", exc, raw)
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
