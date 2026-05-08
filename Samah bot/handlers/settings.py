"""
Handler — Settings
──────────────────
/settings command, toggles, and conversation history deletion.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from middlewares.auth import ensure_user
from database import queries
from utils.keyboards import settings_keyboard, main_menu_keyboard
from utils.texts import get_text

logger = logging.getLogger(__name__)


def _get_lang(context_user_data):
    db_user = context_user_data.get("db_user")
    return db_user.language if db_user else "en"


@ensure_user
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show settings panel."""
    db_user = context.user_data.get("db_user")
    if not db_user:
        return

    lang = db_user.language
    keyboard = settings_keyboard(
        receive_enabled=db_user.receive_messages_enabled,
        allow_anon=db_user.allow_anonymous,
        lang=lang
    )

    text = "⚙️ *Settings / ቅንብሮች*"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@ensure_user
async def toggle_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle receive_messages_enabled."""
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user")
    if not db_user:
        return

    lang = db_user.language
    new_val = not db_user.receive_messages_enabled
    await queries.update_user_settings(
        telegram_id=update.effective_user.id,
        receive_messages_enabled=new_val,
    )
    db_user.receive_messages_enabled = new_val

    keyboard = settings_keyboard(
        receive_enabled=db_user.receive_messages_enabled,
        allow_anon=db_user.allow_anonymous,
        lang=lang
    )
    await query.message.edit_text(
        f"⚙️ *Settings*\n\n✅ _Receiving messages {'enabled' if new_val else 'disabled'}._",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


@ensure_user
async def toggle_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle allow_anonymous."""
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user")
    if not db_user:
        return

    lang = db_user.language
    new_val = not db_user.allow_anonymous
    await queries.update_user_settings(
        telegram_id=update.effective_user.id,
        allow_anonymous=new_val,
    )
    db_user.allow_anonymous = new_val

    keyboard = settings_keyboard(
        receive_enabled=db_user.receive_messages_enabled,
        allow_anon=db_user.allow_anonymous,
        lang=lang
    )
    await query.message.edit_text(
        f"⚙️ *Settings*\n\n✅ _Anonymous messages {'allowed' if new_val else 'blocked'}._",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


@ensure_user
async def delete_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete all conversation/reply history for current user."""
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)

    count = await queries.delete_conversation_history(update.effective_user.id)

    db_user = context.user_data.get("db_user")
    keyboard = settings_keyboard(
        receive_enabled=db_user.receive_messages_enabled if db_user else True,
        allow_anon=db_user.allow_anonymous if db_user else True,
        lang=lang
    )
    await query.message.edit_text(
        get_text("history_deleted", lang, count=count),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
