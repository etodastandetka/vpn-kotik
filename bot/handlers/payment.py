import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.payments.cardlink import create_bill, new_order_id
from app.payments.crypto_pay import create_invoice
from app.services.subscription import create_pending_cardlink_payment, create_pending_crypto_payment
from app.tariffs import get_plan
from bot import texts
from bot.keyboards import pay_method_keyboard, plans_keyboard

router = Router()
log = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("plan:"))
async def cb_plan(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    plan_id = callback.data.split(":", 1)[1]
    plan = get_plan(plan_id)
    if not plan:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return
    text = texts.PLAN_HEADER_TEMPLATE.format(
        title=plan.title,
        desc=plan.description,
        rub=plan.cardlink_amount_rub,
        crypto=plan.crypto_amount,
        asset=plan.crypto_asset,
    )
    await callback.message.edit_text(text, reply_markup=pay_method_keyboard(plan_id))
    await callback.answer()


@router.callback_query(F.data.startswith("pay:cardlink:"))
async def cb_pay_cardlink(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    plan_id = callback.data.split(":", 2)[2]
    plan = get_plan(plan_id)
    if not plan:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return
    if not callback.message:
        await callback.answer("Нет сообщения", show_alert=True)
        return

    tid = callback.from_user.id
    custom = f"{tid}|{plan_id}"
    order_id = new_order_id()
    try:
        bill = await create_bill(
            amount_rub=plan.cardlink_amount_rub,
            shop_id=settings.cardlink_shop_id,
            order_id=order_id,
            custom_payload=custom,
            description=plan.description,
            name=plan.title,
            currency_in="RUB",
            bill_type="normal",
            payer_pays_commission=False,
        )
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return
    except Exception:
        log.exception("cardlink create_bill failed")
        await callback.answer("Ошибка создания счёта Cardlink", show_alert=True)
        return

    bill_id = bill.get("bill_id")
    if bill_id:
        await create_pending_cardlink_payment(
            session,
            telegram_id=tid,
            plan_id=plan_id,
            bill_external_id=str(bill_id),
        )

    pay_url = bill.get("link_page_url") or bill.get("link_url")
    if not pay_url:
        await callback.answer("Нет ссылки оплаты в ответе API", show_alert=True)
        return

    await callback.message.answer(
        texts.PAY_CARD_HTML.format(url=pay_url),
        reply_markup=plans_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay:crypto:"))
async def cb_pay_crypto(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    plan_id = callback.data.split(":", 2)[2]
    plan = get_plan(plan_id)
    if not plan:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return
    tid = callback.from_user.id
    payload = f"{tid}|{plan_id}"
    try:
        inv = await create_invoice(
            amount=plan.crypto_amount,
            asset=plan.crypto_asset,
            description=plan.description,
            payload=payload,
            expires_in=3600,
        )
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return
    except Exception:
        log.exception("create_invoice failed")
        await callback.answer("Ошибка создания счёта", show_alert=True)
        return

    invoice_id = inv.get("invoice_id")
    if invoice_id is not None:
        await create_pending_crypto_payment(
            session,
            telegram_id=tid,
            plan_id=plan_id,
            invoice_external_id=str(invoice_id),
        )

    pay_url = inv.get("pay_url") or inv.get("bot_invoice_url")
    if not pay_url:
        await callback.answer("Нет ссылки оплаты в ответе API", show_alert=True)
        return

    await callback.message.answer(
        texts.PAY_CRYPTO_HTML.format(url=pay_url),
        reply_markup=plans_keyboard(),
    )
    await callback.answer()
