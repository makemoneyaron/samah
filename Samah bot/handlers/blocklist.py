"""
Handler — Blocklist management
───────────────────────────────
/blocklist command: view and unblock users.
"""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from middlewares.auth import ensure_user
from database import queries
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


def _get_lang(context_user_data):
    db_user = context_user_data.get("db_user")
    return db_user.language if db_user else "en"


@ensure_user
async def blocklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's blocklist with unblock options."""
    user = update.effective_user
    if not user:
        return

    lang = _get_lang(context.user_data)
    blocked_ids = await queries.get_blocked_list(user.id)

    if not blocked_ids:
        text = "🚫 *Your Blocklist*\n\n_Your blocklist is empty._" if lang == "en" else "🚫 *የታገዱ ሰሪዎች*\n\n_እስካሁን የታገደ ሰው የለም።_"
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        return

    title = "🚫 *Your Blocklist*" if lang == "en" else "🚫 *የታገዱ ሰሪዎች*"
    lines = [
        title,
        "━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]
    keyboard_rows = []

    for tg_id in blocked_ids:
        blocked_user = await queries.get_user_by_telegram_id(tg_id)
        label = f"@{blocked_user.username}" if blocked_user and blocked_user.username else f"ID: {tg_id}"
        lines.append(f"  🔒 {label}")
        unblock_btn = f"🔓 Unblock {label}" if lang == "en" else f"🔓 {label}ን ከእገዳ አንሳ"
        keyboard_rows.append([
            InlineKeyboardButton(
                unblock_btn,
                callback_data=f"unblock_{tg_id}",
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
async def unblock_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unblock a user from the blocklist."""
    query = update.callback_query
    await query.answer("User unblocked")
    lang = _get_lang(context.user_data)

    try:
        blocked_tg_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        return

    await queries.unblock_user(update.effective_user.id, blocked_tg_id)

    success_text = (
        "🔓 *User unblocked successfully.*\n\n"
        "They can now send you messages again."
    ) if lang == "en" else (
        "🔓 *ተጠቃሚው ከእገዳ ተነስቷል።*\n\n"
        "አሁን መልዕክት ሊልኩልዎ ይችላሉ።"
    )

    await query.message.edit_text(
        success_text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )
