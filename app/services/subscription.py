from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Payment, Subscription, User
from app.subscription_stub import build_config_stub
from app.tariffs import get_plan


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    referrer_telegram_id: int | None = None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(telegram_id=telegram_id)
    if referrer_telegram_id is not None and referrer_telegram_id != telegram_id:
        ref = await session.scalar(select(User).where(User.telegram_id == referrer_telegram_id))
        if ref is not None:
            user.referred_by_id = ref.id
    session.add(user)
    await session.flush()
    return user


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.expires_at > now)
        .order_by(Subscription.expires_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _extend_referrer_reward(session: AsyncSession, referrer_internal_id: int, days: int) -> None:
    referrer = await session.get(User, referrer_internal_id)
    if not referrer:
        return
    now = datetime.now(UTC)
    sub = await get_active_subscription(session, referrer_internal_id)
    if sub is not None and sub.expires_at > now:
        base = sub.expires_at
        if base.tzinfo is None:
            base = base.replace(tzinfo=UTC)
        sub.expires_at = base + timedelta(days=days)
    else:
        referrer.bonus_balance_days += days


async def apply_paid_plan(
    session: AsyncSession,
    *,
    telegram_id: int,
    plan_id: str,
    provider: str,
    external_id: str | None,
    amount: str | None,
    currency: str | None,
    payload: str | None,
) -> bool:
    """
    Idempotent activation. Returns False if this payment was already completed.
    """
    plan = get_plan(plan_id)
    if not plan:
        return False

    user = await get_or_create_user(session, telegram_id)

    if external_id:
        existing = await session.scalar(
            select(Payment).where(Payment.provider == provider, Payment.external_id == external_id)
        )
        if existing is not None:
            if existing.status == "completed":
                return False
            existing.status = "completed"
            existing.amount = amount
            existing.currency = currency
            if payload is not None:
                existing.payload = payload
        else:
            session.add(
                Payment(
                    user_id=user.id,
                    provider=provider,
                    external_id=external_id,
                    status="completed",
                    amount=amount,
                    currency=currency,
                    plan_id=plan_id,
                    payload=payload,
                )
            )
    else:
        session.add(
            Payment(
                user_id=user.id,
                provider=provider,
                external_id=None,
                status="completed",
                amount=amount,
                currency=currency,
                plan_id=plan_id,
                payload=payload,
            )
        )

    await session.flush()

    extra = int(user.bonus_balance_days or 0)
    user.bonus_balance_days = 0
    total_days = plan.days + extra

    now = datetime.now(UTC)
    sub = await get_active_subscription(session, user.id)
    base = sub.expires_at if sub and sub.expires_at > now else now
    if base.tzinfo is None:
        base = base.replace(tzinfo=UTC)
    new_expires = base + timedelta(days=total_days)
    stub = build_config_stub(
        settings.subscription_stub_template,
        telegram_id=telegram_id,
        plan_id=plan_id,
        user_id=user.id,
    )
    session.add(Subscription(user_id=user.id, plan_id=plan_id, expires_at=new_expires, config_stub=stub))

    if not user.first_payment_done:
        if user.referred_by_id is not None and settings.referral_bonus_days > 0:
            await _extend_referrer_reward(session, user.referred_by_id, settings.referral_bonus_days)
        user.first_payment_done = True

    await session.commit()
    return True


async def delete_pending_cardlink_by_bill(session: AsyncSession, bill_id: str) -> None:
    await session.execute(
        delete(Payment).where(
            Payment.provider == "cardlink",
            Payment.external_id == bill_id,
            Payment.status == "pending",
        )
    )


async def create_pending_cardlink_payment(
    session: AsyncSession,
    *,
    telegram_id: int,
    plan_id: str,
    bill_external_id: str,
) -> None:
    user = await get_or_create_user(session, telegram_id)
    existing = await session.scalar(
        select(Payment).where(Payment.provider == "cardlink", Payment.external_id == bill_external_id)
    )
    if existing:
        return
    session.add(
        Payment(
            user_id=user.id,
            provider="cardlink",
            external_id=bill_external_id,
            status="pending",
            plan_id=plan_id,
        )
    )
    await session.commit()


async def create_pending_crypto_payment(
    session: AsyncSession,
    *,
    telegram_id: int,
    plan_id: str,
    invoice_external_id: str,
) -> None:
    user = await get_or_create_user(session, telegram_id)
    existing = await session.scalar(
        select(Payment).where(Payment.provider == "crypto", Payment.external_id == invoice_external_id)
    )
    if existing:
        return
    session.add(
        Payment(
            user_id=user.id,
            provider="crypto",
            external_id=invoice_external_id,
            status="pending",
            plan_id=plan_id,
        )
    )
    await session.commit()
