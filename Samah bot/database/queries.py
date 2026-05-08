"""
Database — CRUD queries
───────────────────────
All database operations go through these async helpers.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional, Sequence

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Apology,
    ApologyStatus,
    BlockedUser,
    Reply,
    Report,
    User,
)
from database.session import async_session


# ═══════════════════════════════════════════════════════════
#  User queries
# ═══════════════════════════════════════════════════════════

async def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    display_name: Optional[str] = None,
) -> User:
    """Return existing user or create a new one."""
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            # Update username / display_name if changed
            if username and user.username != username:
                user.username = username
            if display_name and user.display_name != display_name:
                user.display_name = display_name
            await session.commit()
            return user
        user = User(
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_user_by_username(username: str) -> Optional[User]:
    clean = username.lstrip("@").lower()
    async with async_session() as session:
        stmt = select(User).where(func.lower(User.username) == clean)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def update_user_settings(
    telegram_id: int,
    receive_messages_enabled: Optional[bool] = None,
    allow_anonymous: Optional[bool] = None,
    language: Optional[str] = None,
) -> None:
    async with async_session() as session:
        values: dict = {}
        if receive_messages_enabled is not None:
            values["receive_messages_enabled"] = receive_messages_enabled
        if allow_anonymous is not None:
            values["allow_anonymous"] = allow_anonymous
        if language is not None:
            values["language"] = language
        if values:
            stmt = (
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(**values)
            )
            await session.execute(stmt)
            await session.commit()


async def update_user_language(telegram_id: int, language: str) -> None:
    async with async_session() as session:
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(language=language)
        )
        await session.execute(stmt)
        await session.commit()


async def ban_user(telegram_id: int, banned: bool = True) -> None:
    async with async_session() as session:
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_banned=banned)
        )
        await session.execute(stmt)
        await session.commit()


# ═══════════════════════════════════════════════════════════
#  Block-list queries
# ═══════════════════════════════════════════════════════════

async def block_user(user_telegram_id: int, blocked_telegram_id: int) -> None:
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )).scalar_one()
        exists = (await session.execute(
            select(BlockedUser).where(
                and_(
                    BlockedUser.user_id == user.id,
                    BlockedUser.blocked_telegram_id == blocked_telegram_id,
                )
            )
        )).scalar_one_or_none()
        if not exists:
            session.add(BlockedUser(user_id=user.id, blocked_telegram_id=blocked_telegram_id))
            await session.commit()


async def unblock_user(user_telegram_id: int, blocked_telegram_id: int) -> None:
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )).scalar_one()
        stmt = delete(BlockedUser).where(
            and_(
                BlockedUser.user_id == user.id,
                BlockedUser.blocked_telegram_id == blocked_telegram_id,
            )
        )
        await session.execute(stmt)
        await session.commit()


async def get_blocked_list(user_telegram_id: int) -> list[int]:
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )).scalar_one_or_none()
        if not user:
            return []
        stmt = select(BlockedUser.blocked_telegram_id).where(
            BlockedUser.user_id == user.id
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def is_blocked(user_telegram_id: int, target_telegram_id: int) -> bool:
    blocked = await get_blocked_list(target_telegram_id)
    return user_telegram_id in blocked


# ═══════════════════════════════════════════════════════════
#  Apology queries
# ═══════════════════════════════════════════════════════════

async def create_apology(
    sender_telegram_id: int,
    recipient_username: str,
    message: str,
    formatted_message: str,
    anonymous: bool = True,
    tone: str = "short_simple",
    message_type: str = "apology",
    scheduled_at: Optional[dt.datetime] = None,
) -> Apology:
    async with async_session() as session:
        sender = (await session.execute(
            select(User).where(User.telegram_id == sender_telegram_id)
        )).scalar_one()

        recipient = (await session.execute(
            select(User).where(
                func.lower(User.username) == recipient_username.lstrip("@").lower()
            )
        )).scalar_one_or_none()

        apology = Apology(
            sender_id=sender.id,
            recipient_id=recipient.id if recipient else None,
            recipient_username=recipient_username.lstrip("@").lower(),
            message=message,
            formatted_message=formatted_message,
            anonymous=anonymous,
            tone=tone,
            message_type=message_type,
            status=ApologyStatus.PENDING if recipient else ApologyStatus.PENDING,
            scheduled_at=scheduled_at,
        )
        session.add(apology)
        await session.commit()
        await session.refresh(apology)
        return apology


async def update_apology_status(apology_id: int, status: str) -> None:
    async with async_session() as session:
        values: dict = {"status": status}
        if status == ApologyStatus.DELIVERED:
            values["delivered_at"] = dt.datetime.now(dt.timezone.utc)
        stmt = update(Apology).where(Apology.id == apology_id).values(**values)
        await session.execute(stmt)
        await session.commit()


async def reveal_identity(apology_id: int) -> None:
    async with async_session() as session:
        stmt = (
            update(Apology)
            .where(Apology.id == apology_id)
            .values(identity_revealed=True)
        )
        await session.execute(stmt)
        await session.commit()


async def get_apology(apology_id: int) -> Optional[Apology]:
    async with async_session() as session:
        stmt = select(Apology).where(Apology.id == apology_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_sent_apologies(sender_telegram_id: int, limit: int = 20) -> Sequence[Apology]:
    async with async_session() as session:
        sender = (await session.execute(
            select(User).where(User.telegram_id == sender_telegram_id)
        )).scalar_one_or_none()
        if not sender:
            return []
        stmt = (
            select(Apology)
            .where(Apology.sender_id == sender.id)
            .order_by(Apology.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_received_apologies(recipient_telegram_id: int, limit: int = 20) -> Sequence[Apology]:
    async with async_session() as session:
        recipient = (await session.execute(
            select(User).where(User.telegram_id == recipient_telegram_id)
        )).scalar_one_or_none()
        if not recipient:
            return []
        stmt = (
            select(Apology)
            .where(Apology.recipient_id == recipient.id)
            .order_by(Apology.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_pending_apologies_for_user(username: str) -> Sequence[Apology]:
    """Fetch apologies awaiting delivery for a specific username."""
    clean = username.lstrip("@").lower()
    async with async_session() as session:
        stmt = (
            select(Apology)
            .where(
                and_(
                    func.lower(Apology.recipient_username) == clean,
                    Apology.status == ApologyStatus.PENDING,
                )
            )
            .order_by(Apology.created_at.asc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def count_recent_apologies(sender_telegram_id: int, hours: int = 1) -> int:
    """Count apologies sent by user in the last N hours (rate limiting)."""
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    async with async_session() as session:
        sender = (await session.execute(
            select(User).where(User.telegram_id == sender_telegram_id)
        )).scalar_one_or_none()
        if not sender:
            return 0
        stmt = select(func.count()).select_from(Apology).where(
            and_(
                Apology.sender_id == sender.id,
                Apology.created_at >= since,
            )
        )
        result = await session.execute(stmt)
        return result.scalar() or 0


async def get_last_apology_time(sender_telegram_id: int) -> Optional[dt.datetime]:
    """Return timestamp of the sender's last apology."""
    async with async_session() as session:
        sender = (await session.execute(
            select(User).where(User.telegram_id == sender_telegram_id)
        )).scalar_one_or_none()
        if not sender:
            return None
        stmt = (
            select(Apology.created_at)
            .where(Apology.sender_id == sender.id)
            .order_by(Apology.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# ═══════════════════════════════════════════════════════════
#  Reply queries
# ═══════════════════════════════════════════════════════════

async def create_reply(
    apology_id: int,
    sender_telegram_id: int,
    message: str,
) -> Reply:
    async with async_session() as session:
        sender = (await session.execute(
            select(User).where(User.telegram_id == sender_telegram_id)
        )).scalar_one()
        reply = Reply(
            apology_id=apology_id,
            sender_id=sender.id,
            message=message,
        )
        session.add(reply)
        await session.commit()
        await session.refresh(reply)
        return reply


async def get_replies(apology_id: int) -> Sequence[Reply]:
    async with async_session() as session:
        stmt = (
            select(Reply)
            .where(Reply.apology_id == apology_id)
            .order_by(Reply.created_at.asc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def delete_conversation_history(user_telegram_id: int) -> int:
    """Delete all replies associated with apologies the user is involved in."""
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )).scalar_one_or_none()
        if not user:
            return 0
        # Get all apology IDs where user is sender or recipient
        apology_ids_stmt = select(Apology.id).where(
            (Apology.sender_id == user.id) | (Apology.recipient_id == user.id)
        )
        apology_ids = (await session.execute(apology_ids_stmt)).scalars().all()
        if not apology_ids:
            return 0
        del_stmt = delete(Reply).where(Reply.apology_id.in_(apology_ids))
        result = await session.execute(del_stmt)
        await session.commit()
        return result.rowcount


# ═══════════════════════════════════════════════════════════
#  Report queries
# ═══════════════════════════════════════════════════════════

async def create_report(
    reporter_telegram_id: int,
    reported_telegram_id: int,
    reason: str,
    details: Optional[str] = None,
    apology_id: Optional[int] = None,
) -> Report:
    async with async_session() as session:
        reporter = (await session.execute(
            select(User).where(User.telegram_id == reporter_telegram_id)
        )).scalar_one()
        reported = (await session.execute(
            select(User).where(User.telegram_id == reported_telegram_id)
        )).scalar_one()
        report = Report(
            reporter_id=reporter.id,
            reported_user_id=reported.id,
            reason=reason,
            details=details,
            apology_id=apology_id,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report


async def get_all_reports(limit: int = 50) -> Sequence[Report]:
    async with async_session() as session:
        stmt = select(Report).order_by(Report.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_total_users() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count()).select_from(User))
        return result.scalar() or 0


async def get_total_apologies() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count()).select_from(Apology))
        return result.scalar() or 0
