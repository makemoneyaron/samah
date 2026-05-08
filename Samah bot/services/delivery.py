"""
Service — Delivery
──────────────────
Sends apology/crush messages to recipients through the bot.
Handles the case where a recipient hasn't started the bot.
"""

from __future__ import annotations

import logging
from typing import Optional

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, BadRequest

from database import queries
from database.models import ApologyStatus

logger = logging.getLogger(__name__)


async def deliver_apology(bot: Bot, apology_id: int) -> bool:
    """
    Attempt to deliver an apology to the recipient.
    Returns True if successfully sent, False otherwise.
    """
    apology = await queries.get_apology(apology_id)
    if not apology:
        logger.error("Message %s not found for delivery", apology_id)
        return False

    # Try to find recipient in the database
    recipient = await queries.get_user_by_username(apology.recipient_username)

    if not recipient:
        # Recipient never started the bot — store as pending
        logger.info(
            "Recipient @%s not found. Message %s stays pending.",
            apology.recipient_username,
            apology_id,
        )
        return False

    if not recipient.receive_messages_enabled:
        logger.info("Recipient @%s has disabled incoming messages.", apology.recipient_username)
        await queries.update_apology_status(apology_id, ApologyStatus.FAILED)
        return False

    # Get sender telegram_id
    from database.session import async_session
    from database.models import User
    from sqlalchemy import select
    async with async_session() as session:
        sender = (await session.execute(select(User).where(User.id == apology.sender_id))).scalar_one_or_none()
    
    sender_tg_id = sender.telegram_id if sender else None
    
    if sender_tg_id and await queries.is_blocked(sender_tg_id, recipient.telegram_id):
        logger.info("Sender is blocked by recipient.")
        await queries.update_apology_status(apology_id, ApologyStatus.FAILED)
        return False

    if apology.anonymous and not recipient.allow_anonymous:
        logger.info("Recipient @%s does not allow anonymous messages.", apology.recipient_username)
        await queries.update_apology_status(apology_id, ApologyStatus.FAILED)
        return False

    # Build multi-language keyboard for recipient
    lang = recipient.language
    
    accept_label = "✅ Accept" if lang == "en" else "✅ ተቀበል"
    reply_label = "💬 Reply" if lang == "en" else "💬 መልስ"
    reject_label = "❌ Reject" if lang == "en" else "❌ አትቀበል"
    reveal_label = "🔍 Ask who sent this" if lang == "en" else "🔍 ማን እንደላከው ጠይቅ"
    block_label = "🚫 Block sender" if lang == "en" else "🚫 ላኪውን እገድ"
    report_label = "⚠️ Report abuse" if lang == "en" else "⚠️ ሪፖርት አድርግ"

    keyboard = [
        [
            InlineKeyboardButton(accept_label, callback_data=f"accept_{apology_id}"),
            InlineKeyboardButton(reply_label, callback_data=f"reply_{apology_id}"),
        ],
        [
            InlineKeyboardButton(reject_label, callback_data=f"reject_{apology_id}"),
        ],
    ]
    if apology.anonymous:
        keyboard.append([
            InlineKeyboardButton(reveal_label, callback_data=f"reveal_{apology_id}"),
        ])
    keyboard.append([
        InlineKeyboardButton(block_label, callback_data=f"block_{apology_id}"),
        InlineKeyboardButton(report_label, callback_data=f"report_{apology_id}"),
    ])

    try:
        await bot.send_message(
            chat_id=recipient.telegram_id,
            text=apology.formatted_message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        await queries.update_apology_status(apology_id, ApologyStatus.DELIVERED)
        logger.info("Message %s delivered to @%s", apology_id, apology.recipient_username)
        return True

    except Forbidden:
        logger.warning("Bot blocked by recipient @%s", apology.recipient_username)
        return False
    except Exception as exc:
        logger.error("Delivery error for message %s: %s", apology_id, exc)
        return False


async def deliver_pending_apologies(bot: Bot, username: str) -> int:
    """Deliver any pending messages addressed to joining user."""
    pending = await queries.get_pending_apologies_for_user(username)
    delivered = 0
    for apology in pending:
        recipient = await queries.get_user_by_username(username)
        if recipient:
            from database.session import async_session
            from database.models import Apology as ApologyModel
            from sqlalchemy import update
            async with async_session() as session:
                await session.execute(
                    update(ApologyModel).where(ApologyModel.id == apology.id).values(recipient_id=recipient.id)
                )
                await session.commit()

        if await deliver_apology(bot, apology.id):
            delivered += 1
    return delivered
