from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.tariffs import PLANS
from bot.texts import FAQ_ITEMS


def _btn_label(text: str, max_len: int = 58) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Тарифы", callback_data="nav:plans"),
                InlineKeyboardButton(text="📊 Профиль", callback_data="profile:open"),
            ],
            [
                InlineKeyboardButton(text="🎁 Промокод", callback_data="promo:info"),
                InlineKeyboardButton(text="👥 Рефералка", callback_data="ref:info"),
            ],
            [InlineKeyboardButton(text="📖 Как подключиться", callback_data="howto:open")],
            [InlineKeyboardButton(text="❓ Частые вопросы (FAQ)", callback_data="faq:open")],
            [InlineKeyboardButton(text="❔ Помощь", callback_data="help:open")],
            [InlineKeyboardButton(text="💬 Поддержка", callback_data="support:open")],
        ]
    )


def faq_list_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i, (question, _) in enumerate(FAQ_ITEMS):
        rows.append(
            [InlineKeyboardButton(text=f"❓ {_btn_label(question)}", callback_data=f"faq:item:{i}")]
        )
    rows.append([InlineKeyboardButton(text="« Главное меню", callback_data="nav:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def faq_one_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« К списку вопросов", callback_data="faq:open")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="nav:main")],
        ]
    )


def plans_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for plan in PLANS.values():
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✦ {plan.title} · {plan.cardlink_amount_rub:g} ₽",
                    callback_data=f"plan:{plan.id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(text="📊 Статус подписки", callback_data="sub:status"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="nav:main"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pay_method_keyboard(plan_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Карта (Cardlink)", callback_data=f"pay:cardlink:{plan_id}"),
                InlineKeyboardButton(text="💎 Crypto", callback_data=f"pay:crypto:{plan_id}"),
            ],
            [InlineKeyboardButton(text="« Тарифы", callback_data="nav:plans")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="nav:main")],
        ]
    )


def back_to_plans() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Тарифы", callback_data="nav:plans")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="nav:main")],
        ]
    )


def back_to_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="nav:main")]]
    )


def promo_info_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Ввести промокод", callback_data="promo:enter")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="nav:main")],
        ]
    )


def promo_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Отмена", callback_data="promo:cancel")],
        ]
    )
