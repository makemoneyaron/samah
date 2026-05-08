"""
Handler — /start and onboarding
────────────────────────────────
Welcome flow, pending message delivery, and main menu.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from middlewares.auth import ensure_user
from services.delivery import deliver_pending_apologies
from database.queries import update_user_language
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


@ensure_user
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — check language, then show welcome and deliver pending."""
    user = update.effective_user
    if not user or not update.message:
        return

    db_user = context.user_data.get("db_user")
    
    # If language is not set (default is often 'en', but we can check if they've seen the welcome)
    if not context.user_data.get("language_chosen") and db_user:
        # Show language selection
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇪🇹 Amharic (አማርኛ)", callback_data="set_lang_am"),
            ]
        ])
        from utils.texts import TRANSLATIONS
        await update.message.reply_text(
            TRANSLATIONS["en"]["lang_select"],
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    await _show_main_menu(update, context, db_user)


async def _show_main_menu(update, context, db_user):
    from utils.texts import get_text
    from utils.keyboards import main_menu_keyboard
    from services.delivery import deliver_pending_apologies

    lang = db_user.language if db_user else "en"
    
    # Send welcome
    text = get_text("welcome", lang)
    
    if update.message:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )

    # Deliver pending
    username = update.effective_user.username
    if username:
        await deliver_pending_apologies(context.bot, username)


@ensure_user
async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for setting language."""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.replace("set_lang_", "")
    await update_user_language(update.effective_user.id, lang)
    
    context.user_data["language_chosen"] = True
    db_user = context.user_data.get("db_user")
    if db_user:
        db_user.language = lang
        
    await _show_main_menu(update, context, db_user)
