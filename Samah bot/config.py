"""
Samah Bot — Configuration
─────────────────────────
Central configuration loaded from environment variables.
"""

import os
from pathlib import Path

# ── Telegram ────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "SamahBot")

# ── Admin ───────────────────────────────────────────────────
# Comma-separated Telegram user IDs that have admin privileges
ADMIN_IDS: list[int] = [
    int(uid.strip())
    for uid in os.getenv("ADMIN_IDS", "").split(",")
    if uid.strip().isdigit()
]

# ── Database ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'samahbot.db'}")

# ── Rate Limiting ───────────────────────────────────────────
# Maximum apologies a user can send per hour
RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "5"))
# Cooldown in seconds between apology submissions
APOLOGY_COOLDOWN_SECONDS: int = int(os.getenv("APOLOGY_COOLDOWN_SECONDS", "60"))

# ── Content Moderation ──────────────────────────────────────
MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
MIN_MESSAGE_LENGTH: int = int(os.getenv("MIN_MESSAGE_LENGTH", "5"))

# ── AI Rewriting (optional) ─────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Logging ─────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", str(BASE_DIR / "samahbot.log"))

# ── Deployment ──────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", "8443"))
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")  # e.g. https://your-app.railway.app

# ── Misc ────────────────────────────────────────────────────
INVITATION_LINK: str = f"https://t.me/amsorryforeverythingbot?start=invite"
