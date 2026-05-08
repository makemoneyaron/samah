"""
Database — SQLAlchemy ORM models
────────────────────────────────
Tables: users, apologies, replies, reports
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Enums ───────────────────────────────────────────────────
class ApologyTone:
    FORMAL = "formal"
    EMOTIONAL = "emotional"
    FRIENDLY = "friendly"
    DEEP_REGRET = "deep_regret"
    SHORT_SIMPLE = "short_simple"


class ApologyStatus:
    DRAFT = "draft"
    PENDING = "pending"
    DELIVERED = "delivered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"


class ReportReason:
    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE = "inappropriate"
    THREATS = "threats"
    OTHER = "other"


# ── Base ────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Users ───────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    joined_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    receive_messages_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(2), default="en")  # 'en' or 'am'
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    sent_apologies: Mapped[list["Apology"]] = relationship(
        "Apology", foreign_keys="Apology.sender_id", back_populates="sender", lazy="selectin"
    )
    received_apologies: Mapped[list["Apology"]] = relationship(
        "Apology", foreign_keys="Apology.recipient_id", back_populates="recipient", lazy="selectin"
    )
    blocked_users: Mapped[list["BlockedUser"]] = relationship(
        "BlockedUser", foreign_keys="BlockedUser.user_id", back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} @{self.username}>"


# ── Blocked Users ───────────────────────────────────────────
class BlockedUser(Base):
    __tablename__ = "blocked_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    blocked_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="blocked_users")


# ── Apologies ───────────────────────────────────────────────
class Apology(Base):
    __tablename__ = "apologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    recipient_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    recipient_username: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    formatted_message: Mapped[str] = mapped_column(Text, nullable=False)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    tone: Mapped[str] = mapped_column(String(32), default=ApologyTone.SHORT_SIMPLE)
    message_type: Mapped[str] = mapped_column(String(20), default="apology")  # 'apology' or 'crush'
    status: Mapped[str] = mapped_column(String(20), default=ApologyStatus.PENDING)
    identity_revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    delivered_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sender: Mapped["User"] = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_apologies"
    )
    recipient: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[recipient_id], back_populates="received_apologies"
    )
    replies: Mapped[list["Reply"]] = relationship(
        "Reply", back_populates="apology", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Apology id={self.id} status={self.status}>"


# ── Replies ─────────────────────────────────────────────────
class Reply(Base):
    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    apology_id: Mapped[int] = mapped_column(ForeignKey("apologies.id"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    apology: Mapped["Apology"] = relationship("Apology", back_populates="replies")
    sender: Mapped["User"] = relationship("User")


# ── Reports ─────────────────────────────────────────────────
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reported_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    apology_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("apologies.id"), nullable=True
    )
    reason: Mapped[str] = mapped_column(String(32), default=ReportReason.OTHER)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])
    reported_user: Mapped["User"] = relationship("User", foreign_keys=[reported_user_id])
