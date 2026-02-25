import json
import logging

from django.conf import settings

from .base import AnalysisContext, BaseAIProvider, RecommendationData

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """AI analysis via Google Gemini (gemini-1.5-pro)."""

    provider_name = "gemini"
    MODEL = "gemini-1.5-pro"

    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(
            self.MODEL,
            generation_config={"response_mime_type": "application/json"},
        )

    def analyze(self, context: AnalysisContext) -> RecommendationData:
        prompt = self.build_prompt(context)
        logger.info("Running Gemini analysis for %s", context.symbol)

        response = self._model.generate_content(prompt)
        raw_response = response.text
        return self._parse_response(raw_response, context)

    def _parse_response(self, raw: str, context: AnalysisContext) -> RecommendationData:
        try:
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
            logger.error("Gemini response parse error: %s\nRaw: %s", exc, raw)
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
