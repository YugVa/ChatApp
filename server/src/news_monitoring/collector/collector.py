from dataclasses import dataclass

from telethon import TelegramClient

from news_monitoring.core.config import settings


@dataclass
class Collector:
    client: TelegramClient

    @classmethod
    def build(cls) -> "Collector":
        if settings.telegram_api_id is None or settings.telegram_api_hash is None:
            raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
        client = TelegramClient(settings.telethon_session, settings.telegram_api_id, settings.telegram_api_hash)
        return cls(client=client)

    async def start(self) -> None:
        await self.client.connect()

    async def stop(self) -> None:
        await self.client.disconnect()
