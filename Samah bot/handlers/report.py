"""
Handler — /report command
─────────────────────────
Standalone report flow (outside of apology context).
"""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from middlewares.auth import ensure_user
from database import queries
from services.moderation import validate_username
from utils.texts import get_text
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

REPORT_USERNAME, REPORT_REASON = range(2)


def _get_lang(context_user_data):
    db_user = context_user_data.get("db_user")
    return db_user.language if db_user else "en"


@ensure_user
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start a standalone report."""
    lang = _get_lang(context.user_data)
    text = (
        "⚠️ *Report a User*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please enter the @username of the user you want to report:"
    ) if lang == "en" else (
        "⚠️ *ተጠቃሚን ሪፖርት ያድርጉ*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "እባክዎ ሪፖርት ማድረግ የሚፈልጉትን ተጠቃሚ @username ያስገቡ:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    return REPORT_USERNAME


@ensure_user
async def receive_report_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate the reported username."""
    lang = _get_lang(context.user_data)
    text = update.message.text.strip()
    valid, reason = validate_username(text)
    if not valid:
        await update.message.reply_text(f"⚠️ {reason}")
        return REPORT_USERNAME

    context.user_data["report_username"] = text.lstrip("@").lower()

    # Reuse report keyboard logic but with local labels
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚫 Spam", callback_data="report_spam"),
            InlineKeyboardButton("😠 Harassment", callback_data="report_harassment"),
        ],
        [
            InlineKeyboardButton("⚠️ Inappropriate", callback_data="report_inappropriate"),
            InlineKeyboardButton("🔪 Threats", callback_data="report_threats"),
        ],
        [
            InlineKeyboardButton("📝 Other", callback_data="report_other"),
        ],
    ])
    prompt = "Select the reason for your report:" if lang == "en" else "እባክዎ የሪፖርትዎን ምክንያት ይምረጡ:"
    await update.message.reply_text(
        prompt,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return REPORT_REASON


@ensure_user
async def receive_report_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the report reason."""
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)

    reason = query.data.replace("report_", "")
    reported_username = context.user_data.get("report_username")

    if not reported_username:
        return ConversationHandler.END

    reported_user = await queries.get_user_by_username(reported_username)
    if reported_user:
        await queries.create_report(
            reporter_telegram_id=update.effective_user.id,
            reported_telegram_id=reported_user.telegram_id,
            reason=reason,
        )

    await query.message.edit_text(
        get_text("report_received", lang),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )

    context.user_data.pop("report_username", None)
    return ConversationHandler.END


async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the report flow."""
    lang = _get_lang(context.user_data)
    if update.message:
        await update.message.reply_text(get_text("cancelled", lang), parse_mode="Markdown")
    return ConversationHandler.END


def build_report_conversation() -> ConversationHandler:
    """Build ConversationHandler for standalone reports."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("report", report_command),
        ],
        states={
            REPORT_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_report_username),
            ],
            REPORT_REASON: [
                CallbackQueryHandler(receive_report_reason, pattern=r"^report_"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_report),
        ],
        per_user=True,
        per_chat=True,
    )
