from dataclasses import dataclass

from telegram.ext import Application, CommandHandler

from news_monitoring.core.config import settings


def _parse_allowed_ids() -> set[int]:
    if not settings.bot_allowed_ids:
        return set()
    return {int(item.strip()) for item in settings.bot_allowed_ids.split(",") if item.strip()}


@dataclass
class ControlBot:
    application: Application

    @classmethod
    def build(cls) -> "ControlBot":
        if not settings.bot_token:
            raise RuntimeError("BOT_TOKEN must be set")
        app = Application.builder().token(settings.bot_token).build()
        return cls(application=app)

    def register_handlers(self) -> None:
        self.application.add_handler(CommandHandler("status", self.status))

    async def status(self, update, context) -> None:
        allowed = _parse_allowed_ids()
        if allowed and update.effective_user and update.effective_user.id not in allowed:
            await update.message.reply_text("Access denied")
            return
        await update.message.reply_text("Status: ok")

    def run_polling(self) -> None:
        self.register_handlers()
        self.application.run_polling()
