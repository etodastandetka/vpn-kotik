from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter, Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.promo_referral import count_referrals, redeem_promo
from app.services.subscription import get_active_subscription, get_or_create_user
from app.services.subscription_link import ensure_public_sub_token, subscription_import_url
from bot import texts
from bot.keyboards import back_to_main, main_menu_keyboard, promo_cancel_keyboard, promo_info_keyboard
from bot.states import PromoStates

router = Router()

_PROMPT_MSG_ID = "promo_prompt_message_id"
_PROMPT_CHAT_ID = "promo_prompt_chat_id"


class _PromoCodePlainText(BaseFilter):
    """Не команда — чтобы /start и /help в состоянии промокода шли в общие хендлеры."""

    async def __call__(self, message: Message) -> bool:
        t = (message.text or "").strip()
        return bool(t) and not t.startswith("/")


@router.callback_query(F.data == "nav:main")
async def cb_nav_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.WELCOME_HTML, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "promo:info")
async def cb_promo_info(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.PROMO_INFO_HTML, reply_markup=promo_info_keyboard())
    await callback.answer()


@router.callback_query(F.data == "promo:enter")
async def cb_promo_enter(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PromoStates.waiting_code)
    await callback.message.edit_text(texts.PROMO_ENTER_HTML, reply_markup=promo_cancel_keyboard())
    await state.update_data(
        {
            _PROMPT_CHAT_ID: callback.message.chat.id,
            _PROMPT_MSG_ID: callback.message.message_id,
        }
    )
    await callback.answer()


@router.callback_query(F.data == "promo:cancel")
async def cb_promo_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.PROMO_INFO_HTML, reply_markup=promo_info_keyboard())
    await callback.answer()


async def _finish_promo_same_message(
    message: Message,
    state: FSMContext,
    result_html: str,
) -> None:
    data = await state.get_data()
    await state.clear()
    prompt_mid = data.get(_PROMPT_MSG_ID)
    prompt_cid = data.get(_PROMPT_CHAT_ID)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    if prompt_mid is not None and prompt_cid is not None:
        try:
            await message.bot.edit_message_text(
                chat_id=prompt_cid,
                message_id=prompt_mid,
                text=result_html,
                reply_markup=main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return
        except TelegramBadRequest:
            pass
    await message.answer(result_html, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.HTML)


@router.message(StateFilter(PromoStates.waiting_code), F.text, _PromoCodePlainText())
async def promo_code_received(message: Message, session: AsyncSession, state: FSMContext) -> None:
    raw = message.text.strip()
    _ok, msg = await redeem_promo(session, telegram_id=message.from_user.id, raw_code=raw)
    await _finish_promo_same_message(message, state, msg)


@router.message(StateFilter(PromoStates.waiting_code))
async def promo_waiting_not_text(message: Message, state: FSMContext) -> None:
    await _finish_promo_same_message(
        message,
        state,
        "Нужен <b>текст</b> — код одним сообщением. Или нажмите «Отмена» под сообщением про промокод.",
    )


@router.callback_query(F.data == "ref:info")
async def cb_ref_info(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    me = await callback.bot.get_me()
    if not me.username:
        await callback.answer("У бота нет @username — задайте его в BotFather.", show_alert=True)
        return
    uid = callback.from_user.id
    user = await get_or_create_user(session, uid)
    await session.commit()
    cnt = await count_referrals(session, user.id)
    link = f"https://t.me/{me.username}?start=ref_{uid}"
    text = texts.REFERRAL_HTML_TEMPLATE.format(
        link=f"<code>{link}</code>",
        bonus=settings.referral_bonus_days,
        count=cnt,
    )
    await callback.message.edit_text(text, reply_markup=back_to_main())
    await callback.answer()


@router.callback_query(F.data == "profile:open")
async def cb_profile(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user = await get_or_create_user(session, callback.from_user.id)
    sub = await get_active_subscription(session, user.id)
    bonus = int(user.bonus_balance_days or 0)
    ref_cnt = await count_referrals(session, user.id)
    lines = [
        texts.PROFILE_HEADER,
        "",
        f"🆔 <code>{user.telegram_id}</code>",
        f"🎁 Бонусные дни к оплате: <b>{bonus}</b>",
        f"👥 Приглашено по рефералке: <b>{ref_cnt}</b>",
    ]
    if sub:
        lines.extend(
            [
                "",
                f"📅 Активна до: <code>{sub.expires_at.strftime('%d.%m.%Y %H:%M UTC')}</code>",
                f"📦 Тариф: <code>{sub.plan_id}</code>",
            ]
        )
        stub = (sub.config_stub or "").strip()
        if stub:
            tok = await ensure_public_sub_token(session, user)
            happ_url = subscription_import_url(tok)
            lines.append(
                "\n📲 <b>Ссылка для Happ (подписка):</b>\n"
                f"<code>{happ_url}</code>\n"
                "<i>В Happ: подписка → вставить URL. Это не страница в браузере, а фид для приложения.</i>"
            )
            if stub.startswith("http"):
                lines.append(f'\n🔗 <a href="{stub}">исходный URL панели</a>')
            else:
                lines.append("\n<i>Конфиг задаётся в панели; в БД хранятся строки ссылок или URL панели.</i>")
    else:
        lines.append("\n<i>Подписка не активна — откройте «Тарифы».</i>")
    await session.commit()
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_main(), disable_web_page_preview=True)
    await callback.answer()


@router.message(Command("promo"))
async def cmd_promo(
    message: Message,
    session: AsyncSession,
    command: CommandObject,
    state: FSMContext,
) -> None:
    await state.clear()
    raw = (command.args or "").strip()
    if not raw:
        await message.answer(texts.PROMO_MISSING_ARG, reply_markup=main_menu_keyboard())
        return
    _ok, msg = await redeem_promo(session, telegram_id=message.from_user.id, raw_code=raw)
    await message.answer(msg, reply_markup=main_menu_keyboard())
