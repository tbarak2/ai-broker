from django.apps import AppConfig


class TradingConfig(AppConfig):
    name = "apps.trading"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import apps.trading.signals  # noqa: F401
