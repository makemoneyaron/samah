"""
Middleware — Auth & Registration
────────────────────────────────
Ensures user exists in DB before group/private messages.
Handles automatic user registration.
"""

from __future__ import annotations

import functools
import logging
from typing import Callable, Any

from telegram import Update
from telegram.ext import ContextTypes

from database.queries import get_or_create_user
from utils.texts import get_text

logger = logging.getLogger(__name__)


def ensure_user(func: Callable) -> Callable:
    """
    Decorator to ensure user is registered in DB.
    Checks if user is banned before proceeding.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> Any:
        user = update.effective_user
        if not user:
            return None

        # Fetch or register
        db_user = await get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            display_name=user.full_name,
        )

        # Store in context for handlers to reuse
        context.user_data["db_user"] = db_user
        lang = db_user.language if db_user else "en"

        # Check ban status
        if db_user.is_banned:
            text = get_text("user_banned", lang)
            if update.message:
                await update.message.reply_text(text, parse_mode="Markdown")
            elif update.callback_query:
                await update.callback_query.answer(text, show_alert=True)
            return None

        return await func(update, context, *args, **kwargs)

    return wrapper
