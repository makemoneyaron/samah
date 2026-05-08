"""
Handler — /help
────────────────
Shows command reference and usage guide.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from middlewares.auth import ensure_user
from utils.texts import get_text


@ensure_user
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — display usage instructions."""
    db_user = context.user_data.get("db_user")
    lang = db_user.language if db_user else "en"
    
    text = get_text("help", lang)
    
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, parse_mode="Markdown")
