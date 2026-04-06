from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PromoCode, PromoRedemption, User
from app.services.subscription import get_or_create_user


async def redeem_promo(
    session: AsyncSession,
    *,
    telegram_id: int,
    raw_code: str,
) -> tuple[bool, str]:
    code = raw_code.strip().upper()
    if not code:
        return False, "Введите промокод."

    user = await get_or_create_user(session, telegram_id)

    promo = await session.scalar(select(PromoCode).where(func.upper(PromoCode.code) == code))
    if not promo or not promo.active:
        return False, "Промокод не найден или недоступен."

    if promo.valid_until is not None and promo.valid_until < datetime.now(UTC):
        return False, "Срок действия промокода истёк."

    if promo.max_uses is not None and promo.uses_count >= promo.max_uses:
        return False, "Лимит активаций исчерпан."

    existing = await session.scalar(
        select(PromoRedemption).where(
            PromoRedemption.user_id == user.id,
            PromoRedemption.promo_code_id == promo.id,
        )
    )
    if existing:
        return False, "Вы уже активировали этот промокод."

    user.bonus_balance_days += promo.bonus_days
    promo.uses_count += 1
    session.add(PromoRedemption(user_id=user.id, promo_code_id=promo.id))
    await session.commit()
    return True, f"✅ Промокод принят: <b>+{promo.bonus_days}</b> дн. к следующей оплате."


async def count_referrals(session: AsyncSession, user_id: int) -> int:
    q = select(func.count()).select_from(User).where(User.referred_by_id == user_id)
    return int(await session.scalar(q) or 0)
