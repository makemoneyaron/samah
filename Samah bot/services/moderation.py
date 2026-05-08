"""
Service — Content moderation
─────────────────────────────
Basic content filtering and abuse detection.
"""

from __future__ import annotations

import re
import config

# Simple blocklist (extend as needed)
_BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(kill|murder|suicide|bomb|attack)\b", re.IGNORECASE),
    re.compile(r"\b(n[i1]gg[ae3]r|f[a@]gg?[o0]t)\b", re.IGNORECASE),
]


def is_message_appropriate(text: str) -> tuple[bool, str]:
    """
    Check if a message passes basic content moderation.
    Returns (is_ok, reason).
    """
    if len(text) < config.MIN_MESSAGE_LENGTH:
        return False, f"Message is too short (minimum {config.MIN_MESSAGE_LENGTH} characters)."

    if len(text) > config.MAX_MESSAGE_LENGTH:
        return False, f"Message is too long (maximum {config.MAX_MESSAGE_LENGTH} characters)."

    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(text):
            return False, "Your message contains content that violates our community guidelines."

    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate a Telegram username format.
    Returns (is_valid, reason).
    """
    clean = username.lstrip("@")
    if not clean:
        return False, "Username cannot be empty."
    if len(clean) < 5:
        return False, "Telegram usernames must be at least 5 characters."
    if len(clean) > 32:
        return False, "Telegram usernames cannot exceed 32 characters."
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{3,31}$", clean):
        return False, "Invalid username format. Usernames must start with a letter and contain only letters, numbers, and underscores."
    return True, ""
