"""
Handler — Send Crush (ConversationHandler)
──────────────────────────────────────────
Multi-step flow for expressing admiration.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
from middlewares.auth import ensure_user
from middlewares.rate_limiter import rate_limiter
from services.formatter import format_message, tone_display_name
from services.moderation import validate_username, is_message_appropriate
from services.delivery import deliver_apology
from database import queries
from utils.keyboards import (
    tone_keyboard,
    anonymous_keyboard,
    confirm_send_keyboard,
    main_menu_keyboard,
)
from utils.texts import get_text

logger = logging.getLogger(__name__)

# Conversation states
USERNAME, MESSAGE, ANONYMOUS, TONE, PREVIEW = range(5)


def _get_lang(context_user_data):
    db_user = context_user_data.get("db_user")
    return db_user.language if db_user else "en"


@ensure_user
async def crush_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: /crush or 'Send a Crush' button."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    lang = _get_lang(context.user_data)

    if rate_limiter.is_rate_limited(user.id):
        await update.effective_message.reply_text(get_text("rate_limited", lang))
        return ConversationHandler.END

    prompt = get_text("ask_username_crush", lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(prompt, parse_mode="Markdown")
    else:
        await update.message.reply_text(prompt, parse_mode="Markdown")

    return USERNAME


@ensure_user
async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(context.user_data)
    text = update.message.text.strip()
    valid, reason = validate_username(text)
    if not valid:
        await update.message.reply_text(f"⚠️ {reason}")
        return USERNAME

    context.user_data["crush_recipient"] = text.lstrip("@").lower()
    await update.message.reply_text(get_text("ask_message_crush", lang), parse_mode="Markdown")
    return MESSAGE


@ensure_user
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(context.user_data)
    text = update.message.text.strip()
    ok, reason = is_message_appropriate(text)
    if not ok:
        await update.message.reply_text(f"⚠️ {reason}")
        return MESSAGE

    context.user_data["crush_message"] = text
    await update.message.reply_text(
        get_text("ask_anonymous", lang),
        parse_mode="Markdown",
        reply_markup=anonymous_keyboard(lang),
    )
    return ANONYMOUS


@ensure_user
async def receive_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(context.user_data)
    query = update.callback_query
    await query.answer()

    context.user_data["crush_anonymous"] = (query.data == "anon_yes")
    await query.message.edit_text(
        get_text("ask_tone_crush", lang),
        parse_mode="Markdown",
        reply_markup=tone_keyboard(lang, message_type="crush"),
    )
    return TONE


@ensure_user
async def receive_tone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["crush_tone"] = query.data.replace("tone_", "")
    return await _show_preview(query.message, context)


async def _show_preview(message, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(context.user_data)
    ud = context.user_data
    
    sender_name = None
    if not ud.get("crush_anonymous"):
        db_user = ud.get("db_user")
        sender_name = db_user.display_name if db_user else "Someone"

    formatted = format_message(
        message=ud["crush_message"],
        tone=ud["crush_tone"],
        message_type="crush",
        anonymous=ud.get("crush_anonymous", True),
        sender_name=sender_name,
    )
    ud["crush_formatted"] = formatted

    preview_text = (
        "👁️ *Preview / ቅድመ-ዕይታ:*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        + formatted
    )

    await message.edit_text(
        preview_text,
        parse_mode="Markdown",
        reply_markup=confirm_send_keyboard(lang),
    )
    return PREVIEW


@ensure_user
async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(context.user_data)
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_send":
        ud = context.user_data
        user = query.from_user
        
        apology = await queries.create_apology(
            sender_telegram_id=user.id,
            recipient_username=ud["crush_recipient"],
            message=ud["crush_message"],
            formatted_message=ud["crush_formatted"],
            anonymous=ud.get("crush_anonymous", True),
            tone=ud.get("crush_tone"),
            message_type="crush"
        )
        
        rate_limiter.record(user.id)
        delivered = await deliver_apology(context.bot, apology.id)
        
        text = get_text("sent_success_crush" if delivered else "sent_pending", lang, username=ud["crush_recipient"])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        
        # Cleanup
        for key in ["crush_recipient", "crush_message", "crush_anonymous", "crush_tone", "crush_formatted"]:
            ud.pop(key, None)
        return ConversationHandler.END

    if query.data == "confirm_cancel":
        await query.message.edit_text(get_text("cancelled", lang), reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END
    
    return PREVIEW


def build_crush_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("crush", crush_command),
            CallbackQueryHandler(crush_command, pattern="^menu_crush$"),
        ],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)],
            ANONYMOUS: [CallbackQueryHandler(receive_anonymous, pattern="^anon_")],
            TONE: [CallbackQueryHandler(receive_tone, pattern="^tone_")],
            PREVIEW: [CallbackQueryHandler(handle_confirm, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_user=True,
        per_chat=True,
    )
