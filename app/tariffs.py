from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    id: str
    title: str
    days: int
    cardlink_amount_rub: float
    crypto_asset: str
    crypto_amount: str
    description: str


PLANS: dict[str, Plan] = {
    "month": Plan(
        id="month",
        title="1 месяц",
        days=30,
        cardlink_amount_rub=499.0,
        crypto_asset="USDT",
        crypto_amount="5",
        description="Подписка VPN на 30 дней",
    ),
    "quarter": Plan(
        id="quarter",
        title="3 месяца",
        days=90,
        cardlink_amount_rub=1290.0,
        crypto_asset="USDT",
        crypto_amount="12",
        description="Подписка VPN на 90 дней",
    ),
}


def get_plan(plan_id: str) -> Plan | None:
    return PLANS.get(plan_id)
