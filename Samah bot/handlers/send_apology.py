"""
Handler — Send Apology (ConversationHandler)
─────────────────────────────────────────────
Multi-step flow: username → message → anonymous → tone → preview → confirm
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
from services.ai_rewriter import rewrite_apology, is_ai_available
from services.delivery import deliver_apology
from database import queries
from database.models import ApologyStatus
from utils.keyboards import (
    tone_keyboard,
    anonymous_keyboard,
    confirm_send_keyboard,
    ai_rewrite_keyboard,
    main_menu_keyboard,
)
from utils.texts import get_text

logger = logging.getLogger(__name__)

# Conversation states
USERNAME, MESSAGE, ANONYMOUS, TONE, PREVIEW, AI_OFFER = range(6)


def _get_lang(context_user_data):
    db_user = context_user_data.get("db_user")
    return db_user.language if db_user else "en"


# ── Entry point ─────────────────────────────────────────────

@ensure_user
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: /send or 'Send an Apology' button."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    lang = _get_lang(context.user_data)

    # Rate limiting
    if rate_limiter.is_rate_limited(user.id):
        text = get_text("rate_limited", lang)
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, parse_mode="Markdown")
        return ConversationHandler.END

    cooldown_sec = rate_limiter.seconds_until_next(user.id)
    if cooldown_sec > 0:
        # Note: we should ideally have a translation for cooldown but it works for now
        text = f"⏱️ Wait {cooldown_sec}s"
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, parse_mode="Markdown")
        return ConversationHandler.END

    prompt = get_text("ask_username", lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            prompt, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(prompt, parse_mode="Markdown")

    return USERNAME


# ── Step 1: Receive username ────────────────────────────────

@ensure_user
async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and store the recipient username."""
    lang = _get_lang(context.user_data)
    text = update.message.text.strip()
    valid, reason = validate_username(text)
    if not valid:
        await update.message.reply_text(
            f"⚠️ {reason}\n\nPlease try again:",
            parse_mode="Markdown",
        )
        return USERNAME

    clean_username = text.lstrip("@").lower()

    # Don't allow sending to yourself
    if (
        update.effective_user.username
        and clean_username == update.effective_user.username.lower()
    ):
        await update.message.reply_text(
            "🤍 _You don't need a bot to forgive yourself — just breathe._",
            parse_mode="Markdown",
        )
        return USERNAME

    context.user_data["apology_recipient"] = clean_username
    await update.message.reply_text(get_text("ask_message", lang), parse_mode="Markdown")
    return MESSAGE


# ── Step 2: Receive message ─────────────────────────────────

@ensure_user
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and store the apology message."""
    lang = _get_lang(context.user_data)
    text = update.message.text.strip()
    ok, reason = is_message_appropriate(text)
    if not ok:
        await update.message.reply_text(
            f"⚠️ {reason}\n\n",
            parse_mode="Markdown",
        )
        return MESSAGE

    context.user_data["apology_message"] = text
    await update.message.reply_text(
        get_text("ask_anonymous", lang),
        parse_mode="Markdown",
        reply_markup=anonymous_keyboard(lang),
    )
    return ANONYMOUS


# ── Step 3: Anonymous toggle ────────────────────────────────

@ensure_user
async def receive_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store anonymous preference."""
    lang = _get_lang(context.user_data)
    query = update.callback_query
    await query.answer()

    anonymous = query.data == "anon_yes"
    context.user_data["apology_anonymous"] = anonymous

    await query.message.edit_text(
        get_text("ask_tone", lang),
        parse_mode="Markdown",
        reply_markup=tone_keyboard(lang),
    )
    return TONE


# ── Step 4: Tone selection ──────────────────────────────────

@ensure_user
async def receive_tone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store tone and show preview (with optional AI offer)."""
    lang = _get_lang(context.user_data)
    query = update.callback_query
    await query.answer()

    tone = query.data.replace("tone_", "")
    context.user_data["apology_tone"] = tone

    # If AI is available, offer rewriting
    if is_ai_available():
        await query.message.edit_text(
            "✨ *Would you like AI to refine your message?*\n\n"
            f"Current tone: {tone_display_name(tone)}\n\n"
            "_AI can make your apology sound more sincere and polished._",
            parse_mode="Markdown",
            reply_markup=ai_rewrite_keyboard(lang),
        )
        return AI_OFFER

    # Otherwise, go straight to preview
    return await _show_preview(query.message, context)


# ── Step 4b: AI rewrite offer ───────────────────────────────

@ensure_user
async def handle_ai_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle AI rewrite or skip."""
    query = update.callback_query
    await query.answer()

    if query.data == "ai_rewrite":
        original = context.user_data["apology_message"]
        tone = context.user_data["apology_tone"]

        await query.message.edit_text(
            "✨ _Rewriting your message with AI..._",
            parse_mode="Markdown",
        )

        rewritten = await rewrite_apology(original, tone)
        if rewritten:
            context.user_data["apology_message"] = rewritten
            await query.message.edit_text(
                f"✨ *AI-refined message:*\n\n{rewritten}\n\n"
                "_Proceeding to preview..._",
                parse_mode="Markdown",
            )

    return await _show_preview(query.message, context)


# ── Preview ─────────────────────────────────────────────────

async def _show_preview(message, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and show the formatted preview."""
    lang = _get_lang(context.user_data)
    ud = context.user_data
    sender_name = None
    if not ud.get("apology_anonymous"):
        db_user = ud.get("db_user")
        sender_name = db_user.display_name if db_user else "Unknown"

    formatted = format_message(
        message=ud["apology_message"],
        tone=ud["apology_tone"],
        anonymous=ud.get("apology_anonymous", True),
        sender_name=sender_name,
    )
    context.user_data["apology_formatted"] = formatted

    preview_text = (
        "👁️ *Preview:*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        + formatted
        + f"\n\n📨 *To:* @{ud['apology_recipient']}"
    )

    await message.edit_text(
        preview_text,
        parse_mode="Markdown",
        reply_markup=confirm_send_keyboard(lang),
    )
    return PREVIEW


# ── Confirm / Edit / Cancel ─────────────────────────────────

@ensure_user
async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle preview confirmation buttons."""
    lang = _get_lang(context.user_data)
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "confirm_cancel":
        await query.message.edit_text(get_text("cancelled", lang), parse_mode="Markdown")
        return ConversationHandler.END

    if action == "confirm_edit":
        await query.message.edit_text(
            "✏️ *Rewrite your message:*",
            parse_mode="Markdown",
        )
        return MESSAGE

    if action == "confirm_tone":
        await query.message.edit_text(
            get_text("ask_tone", lang),
            parse_mode="Markdown",
            reply_markup=tone_keyboard(lang),
        )
        return TONE

    if action == "confirm_send":
        return await _do_send(query, context)

    return PREVIEW


async def _do_send(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Execute the actual send."""
    lang = _get_lang(context.user_data)
    ud = context.user_data
    user = query.from_user

    recipient_username = ud["apology_recipient"]
    recipient = await queries.get_user_by_username(recipient_username)

    if recipient:
        if await queries.is_blocked(user.id, recipient.telegram_id):
            await query.message.edit_text("🚫 Blocked", parse_mode="Markdown")
            return ConversationHandler.END

        if not recipient.receive_messages_enabled:
            await query.message.edit_text("🚫 Recipient has disabled messages.", parse_mode="Markdown")
            return ConversationHandler.END

        if ud.get("apology_anonymous") and not recipient.allow_anonymous:
            await query.message.edit_text("🚫 Recipient does not allow anonymous messages.", parse_mode="Markdown")
            return ConversationHandler.END

    apology = await queries.create_apology(
        sender_telegram_id=user.id,
        recipient_username=recipient_username,
        message=ud["apology_message"],
        formatted_message=ud["apology_formatted"],
        anonymous=ud.get("apology_anonymous", True),
        tone=ud.get("apology_tone", "short_simple"),
    )

    rate_limiter.record(user.id)
    delivered = await deliver_apology(context.bot, apology.id)

    if delivered:
        await query.message.edit_text(
            get_text("sent_success", lang, username=recipient_username),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    else:
        invite_link = f"https://t.me/{config.BOT_USERNAME}?start=invite"
        await query.message.edit_text(
            get_text("sent_pending", lang, username=recipient_username, invite_link=invite_link),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )

    # Cleanup
    for key in ["apology_recipient", "apology_message", "apology_anonymous", "apology_tone", "apology_formatted"]:
        context.user_data.pop(key, None)

    return ConversationHandler.END


@ensure_user
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel during conversation."""
    lang = _get_lang(context.user_data)
    if update.message:
        await update.message.reply_text(
            get_text("cancelled", lang),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang),
        )
    return ConversationHandler.END


def build_send_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("send", send_command),
            CallbackQueryHandler(send_command, pattern="^menu_send$"),
        ],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)],
            ANONYMOUS: [CallbackQueryHandler(receive_anonymous, pattern="^anon_")],
            TONE: [CallbackQueryHandler(receive_tone, pattern="^tone_")],
            AI_OFFER: [CallbackQueryHandler(handle_ai_choice, pattern="^ai_")],
            PREVIEW: [CallbackQueryHandler(handle_confirm, pattern="^confirm_")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel, pattern="^confirm_cancel$"),
        ],
        per_user=True,
        per_chat=True,
    )
