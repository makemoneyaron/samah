"""
Service — Apology/Crush formatting
──────────────────────────────────
Turns raw text + tone into a beautifully
formatted Telegram-ready message.
"""

from __future__ import annotations

import datetime as dt


# ── Templates ──────────────────────────────────────────────

_HEADERS: dict[str, dict[str, str]] = {
    "apology": {
        "formal": "📜  *A Formal Apology*",
        "emotional": "💔  *From the Heart*",
        "friendly": "🤝  *A Friendly Note*",
        "deep_regret": "🕊️  *Words of Deep Regret*",
        "short_simple": "💌  *A Simple Apology*",
    },
    "crush": {
        "secret_admirer": "🕶️  *From a Secret Admirer*",
        "romantic": "🌹  *A Romantic Note*",
        "flirty": "✨  *Feeling a Spark*",
        "poetic": "📜  *A Poetic Expression*",
        "direct": "💓  *Straight from the Heart*",
    }
}

_DIVIDER = "─" * 26

_FOOTERS: dict[str, dict[str, str]] = {
    "apology": {
        "formal": "🤍 _Sent with sincerity through Samah Bot_",
        "emotional": "🌙 _Sent with a heavy heart through Samah Bot_",
        "friendly": "✨ _Sent through Samah Bot_",
        "deep_regret": "🕊️ _Sent in hope of peace through Samah Bot_",
        "short_simple": "💌 _Sent via Samah Bot_",
    },
    "crush": {
        "secret_admirer": "🤫 _Your secret is safe with Samah Bot_",
        "romantic": "💖 _Love is in the air via Samah Bot_",
        "flirty": "🦋 _Sent with a smile through Samah Bot_",
        "poetic": "✨ _Artfully sent via Samah Bot_",
        "direct": "💘 _Sincerely sent through Samah Bot_",
    }
}


def format_message(
    message: str,
    tone: str = "short_simple",
    message_type: str = "apology",
    anonymous: bool = True,
    sender_name: str | None = None,
) -> str:
    """
    Return a formatted message string ready for Telegram.
    """
    type_headers = _HEADERS.get(message_type, _HEADERS["apology"])
    header = type_headers.get(tone, type_headers.get(list(type_headers.keys())[0]))
    
    type_footers = _FOOTERS.get(message_type, _FOOTERS["apology"])
    footer = type_footers.get(tone, type_footers.get(list(type_footers.keys())[0]))
    
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%b %d, %Y · %H:%M UTC")

    sender_line = "👤 _From: Anonymous_" if anonymous else f"👤 _From: {sender_name or 'Unknown'}_"

    parts = [
        header,
        _DIVIDER,
        "",
        message,
        "",
        _DIVIDER,
        sender_line,
        f"🕐 _{timestamp}_",
        "",
        footer,
    ]
    return "\n".join(parts)


def tone_display_name(tone: str, message_type: str = "apology") -> str:
    """Human-readable tone label."""
    if message_type == "crush":
        return {
            "secret_admirer": "🕶️ Secret Admirer",
            "romantic": "🌹 Romantic",
            "flirty": "✨ Flirty",
            "poetic": "📜 Poetic",
            "direct": "💓 Direct",
        }.get(tone, tone.replace("_", " ").title())
    
    return {
        "formal": "📜 Formal",
        "emotional": "💔 Emotional",
        "friendly": "🤝 Friendly",
        "deep_regret": "🕊️ Deep Regret",
        "short_simple": "💌 Short & Simple",
    }.get(tone, tone.replace("_", " ").title())
