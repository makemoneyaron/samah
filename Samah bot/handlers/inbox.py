"""
Handler — Inbox & received apologies
─────────────────────────────────────
/inbox command and the menu_inbox button.
"""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from middlewares.auth import ensure_user
from database import queries
from utils.texts import get_text
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


def _get_lang(context_user_data):
    db_user = context_user_data.get("db_user")
    return db_user.language if db_user else "en"


@ensure_user
async def inbox_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show received apologies."""
    user = update.effective_user
    if not user:
        return

    lang = _get_lang(context.user_data)
    apologies = await queries.get_received_apologies(user.id)

    if not apologies:
        text = "📬 *Your Inbox*\n\n_Your inbox is empty._" if lang == "en" else "📬 *የደረሱኝ*\n\n_ምንም የደረሰዎት መልዕክት የለም።_"
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        return

    # Build inbox list
    title = "📬 *Your Inbox*" if lang == "en" else "📬 *የደረሱኝ*"
    lines = [
        title,
        "━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    keyboard_rows = []
    for i, apology in enumerate(apologies[:10], 1):
        status_icon = {
            "delivered": "📩",
            "accepted": "✅",
            "rejected": "❌",
            "pending": "⏳",
        }.get(apology.status, "📩")

        sender_label = "Anonymous" if apology.anonymous and not apology.identity_revealed else f"@{apology.recipient_username}"
        created = apology.created_at.strftime("%b %d, %H:%M") if apology.created_at else "Unknown"
        tone_label = apology.tone.replace("_", " ").title()

        message_type_icon = "💖" if apology.message_type == "crush" else "💌"

        lines.append(
            f"{status_icon} {message_type_icon} *#{apology.id}* · {tone_label}\n"
            f"   From: _{sender_label}_ · {created}\n"
        )
        view_label = f"📖 View #{apology.id}" if lang == "en" else f"📖 # {apology.id}ን እይ"
        keyboard_rows.append([
            InlineKeyboardButton(
                view_label,
                callback_data=f"view_apology_{apology.id}",
            )
        ])

    back_label = "🔙 Back to menu" if lang == "en" else "🔙 ወደ ዋና ሜኑ"
    keyboard_rows.append([
        InlineKeyboardButton(back_label, callback_data="back_menu"),
    ])

    text = "\n".join(lines)
    markup = InlineKeyboardMarkup(keyboard_rows)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)


@ensure_user
async def view_apology_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View a single apology message in full."""
    query = update.callback_query
    await query.answer()
    lang = _get_lang(context.user_data)

    try:
        apology_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        return

    apology = await queries.get_apology(apology_id)
    if not apology:
        await query.message.edit_text("❌ Apology not found.", parse_mode="Markdown")
        return

    # Build detail view
    text = apology.formatted_message

    # Build action buttons
    keyboard = []
    if apology.status == "delivered":
        accept_label = "✅ Accept" if lang == "en" else "✅ ተቀበል"
        reply_label = "💬 Reply" if lang == "en" else "💬 መልስ"
        reject_label = "❌ Reject" if lang == "en" else "❌ አትቀበል"
        
        keyboard.append([
            InlineKeyboardButton(accept_label, callback_data=f"accept_{apology_id}"),
            InlineKeyboardButton(reply_label, callback_data=f"reply_{apology_id}"),
        ])
        keyboard.append([
            InlineKeyboardButton(reject_label, callback_data=f"reject_{apology_id}"),
        ])

    # Thread history
    replies = await queries.get_replies(apology_id)
    if replies:
        thread_title = "💬 *Conversation Thread*" if lang == "en" else "💬 *የውይይት ታሪክ*"
        text += f"\n\n{thread_title}\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        for r in replies[-5:]:  # Show last 5 replies
            created = r.created_at.strftime("%H:%M") if r.created_at else ""
            text += f"  _{created}_ — {r.message}\n"

    back_inbox_label = "🔙 Back to inbox" if lang == "en" else "🔙 ወደ የደረሱኝ"
    keyboard.append([
        InlineKeyboardButton(back_inbox_label, callback_data="menu_inbox"),
    ])

    await query.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
