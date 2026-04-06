from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.exc import OperationalError

from app.database import async_session_maker
from bot import texts
from bot.keyboards import main_menu_keyboard


def _is_db_connect_error(exc: BaseException) -> bool:
    if isinstance(exc, (ConnectionRefusedError, TimeoutError, OSError)):
        return True
    if isinstance(exc, OperationalError):
        return True
    cause = exc.__cause__
    if cause is not None and isinstance(cause, (ConnectionRefusedError, TimeoutError, OSError)):
        return True
    return False


async def _answer_db_down(event: TelegramObject) -> None:
    if isinstance(event, Message):
        await event.answer(texts.DB_UNAVAILABLE_HTML, reply_markup=main_menu_keyboard())
        return
    if isinstance(event, CallbackQuery):
        await event.answer("База данных недоступна. Запустите PostgreSQL.", show_alert=True)
        if event.message:
            await event.message.answer(texts.DB_UNAVAILABLE_HTML, reply_markup=main_menu_keyboard())


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except Exception as exc:
                if not _is_db_connect_error(exc):
                    raise
                await _answer_db_down(event)
                return None
