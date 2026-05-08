"""
Service — AI-assisted rewriting (optional)
──────────────────────────────────────────
Uses OpenAI to refine / improve messages (Apologies & Crushes).
Falls back gracefully when API key is missing.
"""

from __future__ import annotations

import logging

import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None and config.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI
            _client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        except Exception:
            logger.warning("OpenAI client could not be initialised.")
    return _client


SYSTEM_PROMPT = (
    "You are a compassionate and emotionally intelligent writing assistant. "
    "The user will give you a message (either an apology or an expression of a crush) and a tone. "
    "Rewrite the message to sound more sincere, intentional, and clear. "
    "Maintain the user's core message but elevate the writing quality. "
    "Keep it concise — under 200 words. Do NOT add greetings or sign-offs. "
    "Return ONLY the rewritten text."
)


async def rewrite_apology(message: str, tone: str) -> str | None:
    """
    Rewrite the message using AI.
    Works for both apologies and romantic 'crush' messages.
    """
    client = _get_client()
    if client is None:
        return None

    # Consolidated tone instructions for both types
    tone_instruction = {
        # Apology tones
        "formal": "Make it formal, professional, and respectful.",
        "emotional": "Make it deeply emotional, raw, and heartfelt.",
        "friendly": "Make it warm, casual, and friendly.",
        "deep_regret": "Express profound regret, sorrow, and ownership of mistakes.",
        "short_simple": "Keep it short, simple, and sincerely direct.",
        
        # Crush tones
        "secret_admirer": "Make it mysterious, intriguing, and respectful.",
        "romantic": "Make it traditionally romantic and sweet.",
        "flirty": "Make it playful, charming, and showing a spark of interest.",
        "poetic": "Express it with beautiful metaphors and poetic language.",
        "direct": "Make it vulnerable and straight from the heart.",
    }.get(tone, "Improve clarity and sincerity while maintaining the original intent.")

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Tone guidance: {tone_instruction}\n\nOriginal message:\n{message}",
                },
            ],
            max_tokens=300,
            temperature=0.8,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("AI rewrite failed: %s", exc)
        return None


def is_ai_available() -> bool:
    """Check if AI features are configured."""
    return bool(config.OPENAI_API_KEY)
