from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    name = "apps.telegram_bot"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import apps.telegram_bot.signals  # noqa: F401
