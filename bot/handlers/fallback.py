from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import main_menu_keyboard

router = Router()


@router.message(~Command())
async def any_non_command_message(message: Message) -> None:
    hint = (
        "Я пока понимаю только кнопки меню и команды (<code>/start</code>, <code>/help</code>, "
        "<code>/promo КОД</code>). Выберите действие ниже."
    )
    if not message.text:
        hint = "Используйте кнопки меню ниже или команду /start."
    await message.answer(hint, reply_markup=main_menu_keyboard())


@router.callback_query()
async def any_callback(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer()
        return
    await callback.answer(
        "Эта кнопка устарела или недоступна. Откройте главное меню.",
        show_alert=True,
    )
    if callback.message:
        try:
            await callback.message.answer(
                "Откройте меню командой /start или кнопкой ниже.",
                reply_markup=main_menu_keyboard(),
            )
        except Exception:
            pass
