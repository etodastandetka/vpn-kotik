import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.subscription import get_active_subscription, get_or_create_user
from bot import texts
from bot.keyboards import back_to_main, main_menu_keyboard, plans_keyboard

router = Router()
log = logging.getLogger(__name__)


def _parse_ref(args: str | None) -> int | None:
    if not args:
        return None
    arg = args.strip()
    if not arg.startswith("ref_"):
        return None
    try:
        tid = int(arg[4:])
        return tid if tid > 0 else None
    except ValueError:
        return None


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session: AsyncSession,
    command: CommandObject,
    state: FSMContext,
) -> None:
    await state.clear()
    try:
        ref_tid = _parse_ref(command.args)
        await get_or_create_user(session, message.from_user.id, referrer_telegram_id=ref_tid)
        await session.commit()
        await message.answer(texts.WELCOME_HTML, reply_markup=main_menu_keyboard())
    except OperationalError:
        raise  # отдаём в DbSessionMiddleware → текст про недоступную БД
    except Exception:
        log.exception("cmd_start")
        await message.answer(
            "Не удалось открыть профиль. Чаще всего не запущена база <b>PostgreSQL</b> "
            "или неверный <code>DATABASE_URL</code> в .env. Запустите БД и нажмите /start снова.",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == "nav:plans")
async def cb_nav_plans(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "🛒 <b>Тарифы</b>\n\n<i>Выберите период:</i>",
        reply_markup=plans_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "sub:status")
async def cb_sub_status(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user = await get_or_create_user(session, callback.from_user.id)
    await session.commit()
    sub = await get_active_subscription(session, user.id)
    bonus = int(user.bonus_balance_days or 0)
    parts = [
        "📊 <b>Статус подписки</b>",
        "",
        f"🎁 Бонусные дни: <b>{bonus}</b>",
    ]
    if not sub:
        parts.append("\n⚪️ <i>Нет активной подписки.</i>")
    else:
        parts.extend(
            [
                f"✅ До: <code>{sub.expires_at.strftime('%d.%m.%Y %H:%M UTC')}</code>",
                f"📦 План: <code>{sub.plan_id}</code>",
            ]
        )
        if sub.config_stub:
            parts.append(f'\n🔗 <a href="{sub.config_stub}">доступ</a>')
    await callback.message.edit_text(
        "\n".join(parts),
        reply_markup=back_to_main(),
        disable_web_page_preview=True,
    )
    await callback.answer()
