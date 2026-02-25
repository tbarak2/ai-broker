from django.conf import settings
from .base import BaseBroker


def get_broker() -> BaseBroker:
    """
    Factory function that returns the configured broker.
    Set BROKER_BACKEND in settings to switch between paper and real.
    """
    backend = getattr(settings, "BROKER_BACKEND", "paper")

    if backend == "paper":
        from .paper import PaperBroker
        return PaperBroker()
    elif backend == "alpaca":
        # Future: real Alpaca broker
        from .alpaca import AlpacaBroker
        return AlpacaBroker()
    else:
        raise ValueError(f"Unknown broker backend: {backend}. Use 'paper' or 'alpaca'.")
