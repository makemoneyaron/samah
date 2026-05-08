"""
Handler — History (sent apologies)
──────────────────────────────────
/history command and menu_history button.
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
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show sent apology history."""
    user = update.effective_user
    if not user:
        return

    lang = _get_lang(context.user_data)
    apologies = await queries.get_sent_apologies(user.id)

    if not apologies:
        text = "📖 *Sent Messages*\n\n_You haven't sent any messages yet._" if lang == "en" else "📖 *የላኳቸው*\n\n_እስካሁን ምንም መልዕክት አልላኩም።_"
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        return

    title = "📖 *Sent Messages*" if lang == "en" else "📖 *የላኳቸው*"
    lines = [
        title,
        "━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    for apology in apologies[:15]:
        status_icon = {
            "pending": "⏳",
            "delivered": "📩",
            "accepted": "✅",
            "rejected": "❌",
            "failed": "🚫",
        }.get(apology.status, "📩")

        created = apology.created_at.strftime("%b %d, %H:%M") if apology.created_at else "Unknown"
        mode = "🕶️" if apology.anonymous else "👤"
        preview = apology.message[:50] + ("…" if len(apology.message) > 50 else "")
        msg_type = "💖" if apology.message_type == "crush" else "💌"

        lines.append(
            f"{status_icon} {msg_type} *#{apology.id}* → @{apology.recipient_username}\n"
            f"   {mode} · {created}\n"
            f"   _{preview}_\n"
        )

    text = "\n".join(lines)
    back_label = "🔙 Back to menu" if lang == "en" else "🔙 ወደ ዋና ሜኑ"
    keyboard = [[InlineKeyboardButton(back_label, callback_data="back_menu")]]

    if update.message:
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
