"""
Management command to run the Telegram bot.

Usage:
  python manage.py run_telegram_bot
  python manage.py run_telegram_bot --mode webhook --port 8443
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Run the Telegram bot (polling mode for local dev)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--mode",
            choices=["polling", "webhook"],
            default="polling",
            help="Bot mode: polling (dev) or webhook (production)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8443,
            help="Webhook port (only used with --mode webhook)",
        )
        parser.add_argument(
            "--webhook-url",
            type=str,
            default="",
            help="Public webhook URL (e.g. https://yourserver.com/webhook)",
        )

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stderr.write(
                self.style.ERROR(
                    "TELEGRAM_BOT_TOKEN is not set. Add it to your .env file."
                )
            )
            return

        from apps.telegram_bot.bot import run_polling

        mode = options["mode"]
        if mode == "polling":
            self.stdout.write(self.style.SUCCESS("Starting Telegram bot (polling)..."))
            run_polling(token)
        else:
            self.stderr.write(
                self.style.WARNING(
                    "Webhook mode not implemented. Use polling or set up webhook manually."
                )
            )
