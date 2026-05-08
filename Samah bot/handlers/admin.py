"""
Handler — Admin panel
─────────────────────
Admin-only commands: view reports, ban users, stats, broadcast.
"""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
from middlewares.auth import ensure_user
from database import queries

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@ensure_user
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics (admin only)."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 _Unauthorized._", parse_mode="Markdown")
        return

    total_users = await queries.get_total_users()
    total_apologies = await queries.get_total_apologies()
    reports = await queries.get_all_reports(limit=5)

    text = (
        "📊 *Admin Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total users: *{total_users}*\n"
        f"💌 Total apologies: *{total_apologies}*\n"
        f"⚠️ Recent reports: *{len(reports)}*\n"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Reports", callback_data="admin_reports")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
    ])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


@ensure_user
async def admin_view_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View recent reports."""
    query = update.callback_query
    if not _is_admin(update.effective_user.id):
        await query.answer("Unauthorized", show_alert=True)
        return
    await query.answer()

    reports = await queries.get_all_reports(limit=20)

    if not reports:
        await query.message.edit_text(
            "📋 *No reports found.*",
            parse_mode="Markdown",
        )
        return

    lines = ["📋 *Reports*\n━━━━━━━━━━━━━━━━━━━━━━━\n"]
    keyboard_rows = []

    for report in reports:
        created = report.created_at.strftime("%b %d, %H:%M") if report.created_at else "?"
        # Fetch reported user
        from database.session import async_session
        from database.models import User
        from sqlalchemy import select

        async with async_session() as session:
            reported = (await session.execute(
                select(User).where(User.id == report.reported_user_id)
            )).scalar_one_or_none()
            reporter = (await session.execute(
                select(User).where(User.id == report.reporter_id)
            )).scalar_one_or_none()

        reported_label = f"@{reported.username}" if reported and reported.username else f"ID:{report.reported_user_id}"
        reporter_label = f"@{reporter.username}" if reporter and reporter.username else f"ID:{report.reporter_id}"

        lines.append(
            f"  ⚠️ *{reported_label}* reported by {reporter_label}\n"
            f"     Reason: _{report.reason}_ · {created}\n"
        )

        if reported:
            keyboard_rows.append([
                InlineKeyboardButton(
                    f"🔨 Ban {reported_label}",
                    callback_data=f"admin_ban_{reported.telegram_id}",
                ),
            ])

    text = "\n".join(lines)
    markup = InlineKeyboardMarkup(keyboard_rows) if keyboard_rows else None

    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)


@ensure_user
async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user."""
    query = update.callback_query
    if not _is_admin(update.effective_user.id):
        await query.answer("Unauthorized", show_alert=True)
        return
    await query.answer()

    try:
        target_tg_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        return

    await queries.ban_user(target_tg_id, banned=True)

    await query.message.edit_text(
        f"🔨 *User {target_tg_id} has been banned.*\n\n"
        "They can no longer use Samah Bot.",
        parse_mode="Markdown",
    )
    logger.info("Admin %s banned user %s", update.effective_user.id, target_tg_id)


@ensure_user
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start broadcast message input."""
    query = update.callback_query
    if not _is_admin(update.effective_user.id):
        await query.answer("Unauthorized", show_alert=True)
        return
    await query.answer()

    context.user_data["admin_broadcast"] = True
    await query.message.edit_text(
        "📢 *Broadcast*\n\n"
        "Send the message you want to broadcast to all users.\n"
        "Use /cancel to abort.",
        parse_mode="Markdown",
    )


@ensure_user
async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send broadcast message to all users."""
    if not _is_admin(update.effective_user.id):
        return
    if not context.user_data.get("admin_broadcast"):
        return

    text = update.message.text
    context.user_data.pop("admin_broadcast", None)

    # Get all users
    from database.session import async_session
    from database.models import User
    from sqlalchemy import select

    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()

    sent = 0
    failed = 0
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=f"📢 *Announcement from Samah Bot*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n{text}",
                parse_mode="Markdown",
            )
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 *Broadcast complete*\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}",
        parse_mode="Markdown",
    )
    logger.info("Admin broadcast: sent=%d failed=%d", sent, failed)
