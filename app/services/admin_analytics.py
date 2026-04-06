"""Агрегаты для админ-дашборда (БД)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, Subscription, User


async def dashboard_summary(session: AsyncSession) -> dict:
    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    soon = now + timedelta(days=3)

    active_subs = await session.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.expires_at > now)
    )
    users_total = await session.scalar(select(func.count()).select_from(User))

    pay_24h = await session.scalar(
        select(func.count())
        .select_from(Payment)
        .where(Payment.status == "completed", Payment.created_at >= day_ago)
    )
    pay_7d = await session.scalar(
        select(func.count())
        .select_from(Payment)
        .where(Payment.status == "completed", Payment.created_at >= week_ago)
    )

    pending = await session.scalar(
        select(func.count()).select_from(Payment).where(Payment.status == "pending")
    )

    by_provider_7d = await session.execute(
        select(Payment.provider, func.count())
        .where(Payment.status == "completed", Payment.created_at >= week_ago)
        .group_by(Payment.provider)
    )
    provider_rows = {r[0]: int(r[1]) for r in by_provider_7d.all()}

    new_subs_7d = await session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.created_at >= week_ago)
    )

    expiring_soon = await session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.expires_at > now, Subscription.expires_at <= soon)
    )

    referrals = await session.scalar(
        select(func.count()).select_from(User).where(User.referred_by_id.is_not(None))
    )

    return {
        "generated_at": now.isoformat(),
        "users_total": int(users_total or 0),
        "active_subscriptions": int(active_subs or 0),
        "payments_completed_24h": int(pay_24h or 0),
        "payments_completed_7d": int(pay_7d or 0),
        "payments_pending": int(pending or 0),
        "payments_by_provider_7d": provider_rows,
        "subscriptions_created_7d": int(new_subs_7d or 0),
        "subscriptions_expiring_3d": int(expiring_soon or 0),
        "users_with_referrer": int(referrals or 0),
    }


async def payments_breakdown(session: AsyncSession, *, days: int = 7) -> dict:
    now = datetime.now(UTC)
    since = now - timedelta(days=max(1, min(days, 90)))

    rows = await session.execute(
        select(Payment.provider, Payment.status, func.count())
        .where(Payment.created_at >= since)
        .group_by(Payment.provider, Payment.status)
    )
    breakdown: list[dict] = []
    for provider, status, cnt in rows.all():
        breakdown.append(
            {
                "provider": provider,
                "status": status,
                "count": int(cnt),
            }
        )

    return {"since": since.isoformat(), "days": days, "breakdown": breakdown}


def _day_start_utc(dt: datetime) -> datetime:
    d = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return d.replace(hour=0, minute=0, second=0, microsecond=0)


def _fill_daily_series(
    days: int,
    end: datetime,
    pay_by_day: dict[str, int],
    sub_by_day: dict[str, int],
) -> list[dict]:
    end_d = _day_start_utc(end).date()
    start_d = end_d - timedelta(days=days - 1)
    out: list[dict] = []
    current = start_d
    while current <= end_d:
        key = current.isoformat()
        out.append(
            {
                "date": key,
                "payments_completed": int(pay_by_day.get(key, 0)),
                "subscriptions_new": int(sub_by_day.get(key, 0)),
            }
        )
        current += timedelta(days=1)
    return out


def _bucket_date_key(bucket: object) -> str | None:
    if bucket is None:
        return None
    if isinstance(bucket, datetime):
        b = bucket.astimezone(UTC) if bucket.tzinfo else bucket.replace(tzinfo=UTC)
        return b.date().isoformat()
    if isinstance(bucket, date):
        return bucket.isoformat()
    return str(bucket)[:10]


async def analytics_timeseries(session: AsyncSession, *, days: int = 31) -> dict:
    """
    Дневные ряды: завершённые оплаты (продажи) и новые строки подписок.
    """
    now = datetime.now(UTC)
    window = max(1, min(int(days), 90))
    range_start = _day_start_utc(now - timedelta(days=window - 1))

    pay_bucket = func.date_trunc("day", Payment.created_at).label("bucket")
    pay_rows = await session.execute(
        select(
            pay_bucket,
            func.count().label("cnt"),
        )
        .where(
            Payment.status == "completed",
            Payment.created_at >= range_start,
        )
        .group_by(pay_bucket)
    )
    pay_by_day: dict[str, int] = {}
    for bucket, cnt in pay_rows.all():
        key = _bucket_date_key(bucket)
        if key:
            pay_by_day[key] = int(cnt)

    sub_bucket = func.date_trunc("day", Subscription.created_at).label("bucket")
    sub_rows = await session.execute(
        select(
            sub_bucket,
            func.count().label("cnt"),
        )
        .where(Subscription.created_at >= range_start)
        .group_by(sub_bucket)
    )
    sub_by_day: dict[str, int] = {}
    for bucket, cnt in sub_rows.all():
        key = _bucket_date_key(bucket)
        if key:
            sub_by_day[key] = int(cnt)

    daily = _fill_daily_series(window, now, pay_by_day, sub_by_day)

    today_start = _day_start_utc(now)
    month_start = today_start.replace(day=1)

    pay_today = await session.scalar(
        select(func.count())
        .select_from(Payment)
        .where(Payment.status == "completed", Payment.created_at >= today_start)
    )
    pay_month = await session.scalar(
        select(func.count())
        .select_from(Payment)
        .where(Payment.status == "completed", Payment.created_at >= month_start)
    )
    sub_today = await session.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.created_at >= today_start)
    )
    sub_month = await session.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.created_at >= month_start)
    )

    pay_7d = sum(x["payments_completed"] for x in daily[-7:])
    sub_7d = sum(x["subscriptions_new"] for x in daily[-7:])
    pay_30d = sum(x["payments_completed"] for x in daily[-30:])
    sub_30d = sum(x["subscriptions_new"] for x in daily[-30:])

    return {
        "generated_at": now.isoformat(),
        "range_days": window,
        "daily": daily,
        "calendar_today_utc": {
            "payments_completed": int(pay_today or 0),
            "subscriptions_new": int(sub_today or 0),
        },
        "calendar_month_utc": {
            "payments_completed": int(pay_month or 0),
            "subscriptions_new": int(sub_month or 0),
        },
        "rollup": {
            "last_7d_payments": pay_7d,
            "last_7d_subscriptions": sub_7d,
            "last_30d_payments": pay_30d,
            "last_30d_subscriptions": sub_30d,
        },
    }


async def subscriptions_expiring(session: AsyncSession, *, within_days: int = 7, limit: int = 50) -> dict:
    now = datetime.now(UTC)
    until = now + timedelta(days=max(1, min(within_days, 30)))

    q = (
        select(Subscription, User.telegram_id)
        .join(User, User.id == Subscription.user_id)
        .where(Subscription.expires_at > now, Subscription.expires_at <= until)
        .order_by(Subscription.expires_at.asc())
        .limit(limit)
    )
    res = await session.execute(q)
    items: list[dict] = []
    for sub, tg_id in res.all():
        items.append(
            {
                "subscription_id": sub.id,
                "telegram_id": tg_id,
                "plan_id": sub.plan_id,
                "expires_at": sub.expires_at.isoformat(),
            }
        )
    return {"within_days": within_days, "items": items}
