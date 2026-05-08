"""
Handler — Recipient actions (callbacks)
───────────────────────────────────────
Accept, reject, reply, reveal identity, block, report.
"""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler,
)

from middlewares.auth import ensure_user
from database import queries
from database.models import ApologyStatus
from utils.keyboards import (
    reveal_request_keyboard,
    report_reason_keyboard,
    main_menu_keyboard,
)
from utils.texts import get_text

logger = logging.getLogger(__name__)

# Conversation state for reply
REPLY_TEXT = 0


def _get_lang(context_user_data):
    db_user = context_user_data.get("db_user")
    return db_user.language if db_user else "en"


@ensure_user
async def accept_apology(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recipient accepts an apology."""
    query = update.callback_query
    lang = _get_lang(context.user_data)
    await query.answer("Accepted 🤍")

    try:
        apology_id = int(query.data.split("_")[-1])
        apology = await queries.get_apology(apology_id)
        if not apology: return
        await queries.update_apology_status(apology_id, ApologyStatus.ACCEPTED)
        
        line = "\n\n✅ _You accepted this message._" if lang == "en" else "\n\n✅ _ይህን መልዕክት ተቀብለዋል።_"
        await query.message.edit_text(query.message.text + line, parse_mode="Markdown")
        
        # Notify sender
        async with queries.async_session() as session:
            from database.models import User
            from sqlalchemy import select
            sender = (await session.execute(select(User).where(User.id == apology.sender_id))).scalar_one_or_none()
            if sender:
                text = "✅ *Your message was accepted!*" if sender.language == "en" else "✅ *መልዕክትዎ ተቀባይነት አግኝቷል!*"
                await context.bot.send_message(chat_id=sender.telegram_id, text=text, parse_mode="Markdown", reply_markup=main_menu_keyboard(sender.language))
    except Exception: pass


@ensure_user
async def reject_apology(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recipient rejects an apology."""
    query = update.callback_query
    lang = _get_lang(context.user_data)
    await query.answer("Declined")

    try:
        apology_id = int(query.data.split("_")[-1])
        await queries.update_apology_status(apology_id, ApologyStatus.REJECTED)
        line = "\n\n❌ _You declined this message._" if lang == "en" else "\n\n❌ _ይህን መልዕክት አልተቀበሉትም።_"
        await query.message.edit_text(query.message.text + line, parse_mode="Markdown")
    except Exception: pass


@ensure_user
async def request_reveal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recipient asks to know who sent the apology."""
    query = update.callback_query
    lang = _get_lang(context.user_data)
    await query.answer()

    try:
        apology_id = int(query.data.split("_")[-1])
        apology = await queries.get_apology(apology_id)
        if not apology or not apology.anonymous: return

        async with queries.async_session() as session:
            from database.models import User
            from sqlalchemy import select
            sender = (await session.execute(select(User).where(User.id == apology.sender_id))).scalar_one_or_none()
            if sender:
                req_text = f"🔍 # {apology_id} ለማንነት መገለጥ ጥያቄ ቀርቦለታል።" if sender.language == "am" else f"🔍 A reveal request was sent for your message #{apology_id}."
                await context.bot.send_message(chat_id=sender.telegram_id, text=req_text, parse_mode="Markdown", reply_markup=reveal_request_keyboard(apology_id, sender.language))
                sent_text = "\n\n🔍 _Reveal request sent._" if lang == "en" else "\n\n🔍 _የማንነት መገለጥ ጥያቄ ተልኳል።_"
                await query.message.edit_text(query.message.text + sent_text, parse_mode="Markdown")
    except Exception: pass


@ensure_user
async def do_reveal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)

    try:
        apology_id = int(query.data.split("_")[-1])
        apology = await queries.get_apology(apology_id)
        if not apology: return
        await queries.reveal_identity(apology_id)
        
        await query.message.edit_text("👤 _Identity revealed._" if lang == "en" else "👤 _ማንነትዎ ተገልጿል።_", parse_mode="Markdown")
        
        async with queries.async_session() as session:
            from database.models import User
            from sqlalchemy import select
            recipient = (await session.execute(select(User).where(User.id == apology.recipient_id))).scalar_one_or_none()
            if recipient:
                user = update.effective_user
                notif = f"👤 # {apology_id} የተላከው በ: {user.full_name} (@{user.username}) ነው።" if recipient.language == "am" else f"👤 Identity revealed for #{apology_id}: It's {user.full_name} (@{user.username})!"
                await context.bot.send_message(chat_id=recipient.telegram_id, text=notif, parse_mode="Markdown")
    except Exception: pass


@ensure_user
async def stay_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)
    await query.message.edit_text("🕶️ _Identity stays private._" if lang == "en" else "🕶️ _ማንነትዎ በሚስጥር ይቆያል።_", parse_mode="Markdown")


@ensure_user
async def block_sender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Blocked")
    try:
        apology_id = int(query.data.split("_")[-1])
        apology = await queries.get_apology(apology_id)
        if apology:
            async with queries.async_session() as session:
                from database.models import User
                from sqlalchemy import select
                sender = (await session.execute(select(User).where(User.id == apology.sender_id))).scalar_one_or_none()
                if sender:
                    await queries.block_user(update.effective_user.id, sender.telegram_id)
            await query.message.edit_text(query.message.text + "\n\n🚫 _Sender blocked._", parse_mode="Markdown")
    except Exception: pass


@ensure_user
async def report_abuse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)
    try:
        apology_id = int(query.data.split("_")[-1])
        text = "⚠️ *Report Abuse*\n\nPlease select a reason:" if lang == "en" else "⚠️ *ሪፖርት ያድርጉ*\n\nምክንያት ይምረጡ:"
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=report_reason_keyboard(apology_id, lang))
    except Exception: pass


@ensure_user
async def submit_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)
    try:
        parts = query.data.split("_")
        reason, apology_id = parts[1], int(parts[2])
        apology = await queries.get_apology(apology_id)
        if apology:
            async with queries.async_session() as session:
                from database.models import User
                from sqlalchemy import select
                sender = (await session.execute(select(User).where(User.id == apology.sender_id))).scalar_one_or_none()
                if sender:
                    await queries.create_report(update.effective_user.id, sender.telegram_id, reason, apology_id)
        await query.message.edit_text(get_text("report_received", lang), parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
    except Exception: pass


@ensure_user
async def start_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)
    try:
        apology_id = int(query.data.split("_")[-1])
        context.user_data["replying_to"] = apology_id
        await query.message.edit_text("💬 *Write your reply:*" if lang == "en" else "💬 *መልስዎን ይጻፉ:*", parse_mode="Markdown")
        return REPLY_TEXT
    except Exception: return ConversationHandler.END


@ensure_user
async def receive_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(context.user_data)
    text = update.message.text.strip()
    apology_id = context.user_data.get("replying_to")
    if not apology_id: return ConversationHandler.END
    
    apology = await queries.get_apology(apology_id)
    if not apology: return ConversationHandler.END
    await queries.create_reply(apology_id, update.effective_user.id, text)
    
    try:
        async with queries.async_session() as session:
            from database.models import User
            from sqlalchemy import select
            sender_user = (await session.execute(select(User).where(User.id == apology.sender_id))).scalar_one_or_none()
            recipient_user = (await session.execute(select(User).where(User.id == apology.recipient_id))).scalar_one_or_none()
            target = sender_user if update.effective_user.id != sender_user.telegram_id else recipient_user
            if target:
                await context.bot.send_message(chat_id=target.telegram_id, text=f"💬 *New Reply (# {apology_id})*\n\n{text}", parse_mode="Markdown")
    except Exception: pass

    await update.message.reply_text("✅ *Reply sent!*" if lang == "en" else "✅ *መልስዎ ተልኳል!*", parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


def build_reply_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_reply, pattern=r"^reply_\d+$")],
        states={REPLY_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reply_text)]},
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        per_user=True, per_chat=True,
    )
