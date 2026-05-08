"""
Samah Bot — Main Entry Point
─────────────────────────────
🕊️ A safe emotional bridge between people.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import config
from database import init_db
from utils.logging_setup import setup_logging

# ── Handlers ────────────────────────────────────────────────
from handlers.start import start_command, handle_language_selection
from handlers.help import help_command
from handlers.send_apology import build_send_conversation
from handlers.send_crush import build_crush_conversation
from handlers.inbox import inbox_command, view_apology_detail
from handlers.history import history_command
from handlers.settings import (
    settings_command,
    toggle_receive,
    toggle_anonymous,
    delete_history,
)
from handlers.recipient_actions import (
    accept_apology,
    reject_apology,
    request_reveal,
    do_reveal,
    stay_anonymous,
    block_sender,
    report_abuse,
    submit_report,
    build_reply_conversation,
)
from handlers.blocklist import blocklist_command, unblock_user_handler
from handlers.report import build_report_conversation
from handlers.admin import (
    admin_stats,
    admin_view_reports,
    admin_ban,
    admin_broadcast_start,
    admin_broadcast_send,
)

logger = logging.getLogger(__name__)


# ── Error handler ───────────────────────────────────────────

async def error_handler(update: object, context) -> None:
    """Global error handler — logs exceptions gracefully."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "🤍 _Something went wrong. Please try again._",
                parse_mode="Markdown",
            )
        except Exception:
            pass


# ── Back to menu callback ──────────────────────────────────

async def back_to_menu(update: Update, context) -> None:
    """Handle 'Back to menu' button across all screens."""
    query = update.callback_query
    await query.answer()
    
    from utils.texts import get_text
    from utils.keyboards import main_menu_keyboard
    from database.queries import get_user_by_telegram_id
    
    db_user = await get_user_by_telegram_id(update.effective_user.id)
    lang = db_user.language if db_user else "en"

    await query.message.edit_text(
        get_text("welcome", lang),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang),
    )


# ── Application builder ────────────────────────────────────

def build_application() -> Application:
    """Build and configure the Telegram Application."""
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set. Please set it in your .env file.")
        sys.exit(1)

    app = Application.builder().token(config.BOT_TOKEN).build()

    # ── Conversation handlers (must be added first — they have priority) ──
    app.add_handler(build_send_conversation(), group=0)
    app.add_handler(build_crush_conversation(), group=1)
    app.add_handler(build_reply_conversation(), group=2)
    app.add_handler(build_report_conversation(), group=3)

    # ── Command handlers ────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("inbox", inbox_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("crush", lambda u, c: None)) # Handled by ConversationHandler
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("blocklist", blocklist_command))
    app.add_handler(CommandHandler("admin", admin_stats))

    # ── Language selection ──────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_language_selection, pattern="^set_lang_"))

    # ── Menu button callbacks ───────────────────────────────
    app.add_handler(CallbackQueryHandler(inbox_command, pattern="^menu_inbox$"))
    app.add_handler(CallbackQueryHandler(history_command, pattern="^menu_history$"))
    app.add_handler(CallbackQueryHandler(settings_command, pattern="^menu_settings$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="^menu_help$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_menu$"))

    # ── Settings toggles ────────────────────────────────────
    app.add_handler(CallbackQueryHandler(toggle_receive, pattern="^toggle_receive$"))
    app.add_handler(CallbackQueryHandler(toggle_anonymous, pattern="^toggle_anon$"))
    app.add_handler(CallbackQueryHandler(delete_history, pattern="^delete_history$"))

    # ── Recipient action callbacks ──────────────────────────
    app.add_handler(CallbackQueryHandler(accept_apology, pattern=r"^accept_\d+$"))
    app.add_handler(CallbackQueryHandler(reject_apology, pattern=r"^reject_\d+$"))
    app.add_handler(CallbackQueryHandler(request_reveal, pattern=r"^reveal_\d+$"))
    app.add_handler(CallbackQueryHandler(do_reveal, pattern=r"^do_reveal_\d+$"))
    app.add_handler(CallbackQueryHandler(stay_anonymous, pattern=r"^stay_anon_\d+$"))
    app.add_handler(CallbackQueryHandler(block_sender, pattern=r"^block_\d+$"))
    app.add_handler(CallbackQueryHandler(report_abuse, pattern=r"^report_\d+$"))
    app.add_handler(CallbackQueryHandler(submit_report, pattern=r"^rr_"))
    app.add_handler(CallbackQueryHandler(view_apology_detail, pattern=r"^view_apology_\d+$"))

    # ── Blocklist callbacks ─────────────────────────────────
    app.add_handler(CallbackQueryHandler(unblock_user_handler, pattern=r"^unblock_\d+$"))

    # ── Admin callbacks ─────────────────────────────────────
    app.add_handler(CallbackQueryHandler(admin_view_reports, pattern="^admin_reports$"))
    app.add_handler(CallbackQueryHandler(admin_ban, pattern=r"^admin_ban_\d+$"))
    app.add_handler(CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$"))

    # ── Admin broadcast text (catch-all for admins in broadcast mode) ──
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send),
        group=10,
    )

    # ── Error handler ───────────────────────────────────────
    app.add_error_handler(error_handler)

    return app


async def post_init(application: Application) -> None:
    """Run after the application is initialised (create DB tables)."""
    await init_db()
    logger.info("🕊️  Database initialised.")
    logger.info("🕊️  Samah Bot is ready.")


def main() -> None:
    """Entry point — start the bot."""
    setup_logging()
    logger.info("🕊️  Starting Samah Bot…")

    app = build_application()
    app.post_init = post_init

    if config.WEBHOOK_URL:
        logger.info("Starting in webhook mode at %s", config.WEBHOOK_URL)
        app.run_webhook(
            listen="0.0.0.0",
            port=config.PORT,
            url_path=config.BOT_TOKEN,
            webhook_url=f"{config.WEBHOOK_URL}/{config.BOT_TOKEN}",
        )
    else:
        logger.info("Starting in polling mode…")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )


if __name__ == "__main__":
    main()
