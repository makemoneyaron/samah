"""
Utility — Text constants with Multi-language support
────────────────────────────────────────────────────
Returns strings based on user's preferred language.
"""

# Support Handle
SUPPORT_HANDLE = "@Aaronzuck"

# ── Translations ───────────────────────────────────────────

TRANSLATIONS = {
    "en": {
        "welcome": (
            "🕊️ *Welcome to Samah Bot*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Samah is a safe, emotional bridge between people.\n\n"
            "Send heartfelt apologies, reconciliation messages, "
            "and secret crushes — anonymously or with your name.\n\n"
            "💌  *Send an Apology* — apologize & reconcile\n"
            "💖  *Send a Crush* — express your feelings\n"
            "📬  *Inbox* — view messages you've received\n"
            "📖  *History* — review your sent messages\n"
            "⚙️  *Settings* — control your privacy\n\n"
            "_Choose an option below to get started._"
        ),
        "ask_username_crush": (
            "💖 *Who is your crush?*\n\n"
            "Please enter their Telegram @username.\n"
            "_Example: @username_"
        ),
        "ask_message_crush": "✍️ *Write your secret message*\n\nTell them how you feel. ✨\n_Minimum 5 characters._",
        "ask_tone_crush": "🎨 *Choose a romantic tone*\n\nHow do you want to express your feelings?",
        "sent_success_crush": "✅ *Crush sent successfully!*\n\n💖 Your message has been delivered to @{username}.\nWho knows where this might lead? ✨",
        "help": (
            "❓ *Samah Bot — Help*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "*Commands*\n"
            "/start — Open the main menu\n"
            "/send — Send an apology\n"
            "/crush — Send a crush\n"
            "/inbox — View received messages\n"
            "/history — View sent messages\n"
            "/settings — Privacy & preferences\n"
            "/help — Show this help message\n\n"
            f"🆘 Need support? Contact {SUPPORT_HANDLE}\n\n"
            "🤍 _Built with empathy._"
        ),
        "lang_select": "🌍 *Please select your language / እባክዎን ቋንቋዎን ይምረጡ*",
        "cancelled": "❌ Action cancelled.",
        "error_generic": f"⚠️ *Something went wrong*\n\nPlease try again later. If issues persist, contact {SUPPORT_HANDLE}.",
        "rate_limited": "⏱️ *Please slow down*\n\nYou've reached the sending limit. Please wait a moment.",
        "user_banned": f"🚫 *Your account has been restricted*\n\nIf you believe this is a mistake, contact {SUPPORT_HANDLE}.",
        "history_deleted": "🗑️ *History deleted*\n\n{count} messages removed.",
        "ask_username": "👤 *Who would you like to send this to?*\n\nType @username:",
        "ask_message": "✍️ *Write your message*\n\n_Minimum 5 characters._",
        "ask_anonymous": "🕶️ *How would you like to send this?*\n\nChoose anonymity:",
        "ask_tone": "🎨 *Choose a tone*",
        "sent_success": "✅ *Sent successfully!*",
        "sent_pending": "⏳ *Pending delivery — they haven't joined yet.*",
    },
    "am": {
        "welcome": (
            "🕊️ *እንኳን ወደ ሰማህ ቦት በሰላም መጡ*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "ሰማህ በሰዎች መካከል ደህንነቱ የተጠበቀ ስሜታዊ ድልድይ ነው።\n\n"
            "ይቅርታዎችን፣ እርቆችን እና የፍቅር (Crush) መልዕክቶችን — በስምዎ ወይም በምስጢር ይላኩ።\n\n"
            "💌  *ይቅርታ ላክ* — ይቅርታ ይጠይቁ\n"
            "💖  *የፍቅር መልዕክት ላክ* — ስሜትዎን ይግለጹ\n"
            "📬  *የደረሱኝ* — የደረሱዎትን ይመልከቱ\n"
            "📖  *ታሪክ* — የላኳቸውን ይመልከቱ\n"
            "⚙️  *ቅንብሮች* — ግላዊነትዎን ይቆጣጠሩ\n\n"
            "_ለመጀመር ከታች ካሉት አማራጮች አንዱን ይምረጡ።_"
        ),
        "ask_username_crush": (
            "💖 *ፍቅረኛዎ (Crush) ማነው?*\n\n"
            "እባክዎ የቴሌግራም መለያቸውን (@username) ያስገቡ።\n"
            "_ምሳሌ: @username_"
        ),
        "ask_message_crush": "✍️ *የምስጢር መልዕክትዎን ይጻፉ*\n\nምን እንደሚሰማዎት ይግለጹላቸው። ✨",
        "ask_tone_crush": "🎨 *የፍቅር ድምጸ-ከል (Tone) ይምረጡ*",
        "sent_success_crush": "✅ *መልዕክትዎ ተልኳል!*\n\n💖 መልዕክትዎ ለ@{username} ደርሷል። ✨",
        "help": (
            "❓ *ሰማህ ቦት — እርዳታ*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🆘 ድጋፍ ይፈልጋሉ? {SUPPORT_HANDLE} ያግኙ\n\n"
            "🤍 _በመተሳሰብ የተገነባ።_"
        ),
        "lang_select": "🌍 *ቋንቋ ይምረጡ*",
        "cancelled": "❌ ተሰርዟል።",
        "error_generic": f"⚠️ *ችግር ተፈጥሯል* — {SUPPORT_HANDLE} ያግኙ።",
        "rate_limited": "⏱️ *እባክዎ ፍጥነትዎን ይቀንሱ*",
        "user_banned": "🚫 *መለያዎ ታግዷል*",
        "history_deleted": "🗑️ *ታሪክ ተሰርዟል*",
        "ask_username": "👤 *ለማን መላክ ይፈልጋሉ?*",
        "ask_message": "✍️ *መልዕክትዎን ይጻፉ*",
        "ask_anonymous": "🕶️ *እንዴት መላክ ይፈልጋሉ?*",
        "ask_tone": "🎨 *ድምጸ-ከል ይምረጡ*",
        "sent_success": "✅ *ተልኳል!*",
        "sent_pending": "⏳ *ቆይታ ላይ ነው (እስካሁን አልገቡም)*",
    }
}


def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """Helper to retrieve translated text."""
    lang_batch = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_batch.get(key, TRANSLATIONS["en"].get(key, f"Missing text: {key}"))
    if kwargs:
        return text.format(**kwargs)
    return text
