from aiogram import Router

from bot.handlers import fallback, help_faq, payment, promo_referral, start

router = Router()
router.include_router(start.router)
router.include_router(help_faq.router)
router.include_router(promo_referral.router)
router.include_router(payment.router)
router.include_router(fallback.router)
