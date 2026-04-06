from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from bot import texts
from bot.keyboards import (
    back_to_main,
    faq_list_keyboard,
    faq_one_keyboard,
    main_menu_keyboard,
)

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.HELP_HTML, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "help:open")
async def cb_help_open(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.HELP_HTML, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "howto:open")
async def cb_howto(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.HOWTO_HTML, reply_markup=back_to_main())
    await callback.answer()


@router.callback_query(F.data == "faq:open")
async def cb_faq_open(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.FAQ_INTRO_HTML, reply_markup=faq_list_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("faq:item:"))
async def cb_faq_item(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        idx = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка", show_alert=True)
        return
    if idx < 0 or idx >= len(texts.FAQ_ITEMS):
        await callback.answer("Нет такого вопроса", show_alert=True)
        return
    question, answer = texts.FAQ_ITEMS[idx]
    body = f"<b>{question}</b>\n\n{answer}"
    await callback.message.edit_text(body, reply_markup=faq_one_keyboard())
    await callback.answer()


@router.callback_query(F.data == "support:open")
async def cb_support(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = texts.support_html(settings.support_username, settings.support_info_url)
    await callback.message.edit_text(text, reply_markup=back_to_main(), disable_web_page_preview=False)
    await callback.answer()
