import logging
from typing import List

from django.conf import settings

from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """
    Factory for creating AI provider instances (Strategy pattern).
    Only instantiates providers that have an API key configured.
    """

    _registry = {
        "claude": "core.ai_providers.claude_provider.ClaudeProvider",
        "openai": "core.ai_providers.openai_provider.OpenAIProvider",
        "gemini": "core.ai_providers.gemini_provider.GeminiProvider",
    }

    @classmethod
    def create(cls, provider_name: str) -> BaseAIProvider:
        """Create a single AI provider by name."""
        if provider_name not in cls._registry:
            raise ValueError(
                f"Unknown AI provider: '{provider_name}'. "
                f"Valid options: {list(cls._registry.keys())}"
            )

        module_path, class_name = cls._registry[provider_name].rsplit(".", 1)
        import importlib
        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)
        return provider_class()

    @classmethod
    def create_configured(cls, provider_names: List[str]) -> List[BaseAIProvider]:
        """
        Create all providers that are both requested and have API keys configured.
        Skips providers with missing API keys without raising errors.
        """
        key_map = {
            "claude": settings.ANTHROPIC_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "gemini": settings.GEMINI_API_KEY,
        }
        providers = []
        for name in provider_names:
            if not key_map.get(name):
                logger.warning("Skipping AI provider '%s': no API key configured", name)
                continue
            try:
                providers.append(cls.create(name))
            except Exception as exc:
                logger.error("Failed to initialize AI provider '%s': %s", name, exc)
        return providers
