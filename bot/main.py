import asyncio
import logging
import sys
from pathlib import Path

# Запуск из папки bot/: python main.py — без этого не находится пакет app
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from bot.handlers import router
from bot.middlewares import DbSessionMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    log = logging.getLogger(__name__)
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")
    log.info(
        "Запуск polling. Должен работать только один процесс на этот BOT_TOKEN. "
        "Если в логе Conflict — закройте другие окна/серверы с этим ботом или снимите webhook в BotFather."
    )
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Иначе Conflict, если у бота был webhook или другой клиент держал getUpdates
    await bot.delete_webhook(drop_pending_updates=False)
    log.info("Webhook снят, дальше только long polling.")
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Остановлено (Ctrl+C).")
