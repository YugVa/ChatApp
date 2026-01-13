import argparse
import asyncio

from news_monitoring.api.main import app
from news_monitoring.collector.collector import Collector
from news_monitoring.control_bot.bot import ControlBot
from news_monitoring.core.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="News monitoring server utilities")
    parser.add_argument("command", choices=["api", "collector", "bot"], help="Component to run")
    return parser


async def _run_collector() -> None:
    collector = Collector.build()
    await collector.start()
    await collector.client.run_until_disconnected()


def main() -> None:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "api":
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
        return

    if args.command == "collector":
        asyncio.run(_run_collector())
        return

    if args.command == "bot":
        bot = ControlBot.build()
        bot.run_polling()
        return


if __name__ == "__main__":
    main()
