"""
Utility — Inline keyboard builders with Multi-language support
─────────────────────────────────────────────────────────────
Centralised keyboard layouts with translated labels.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Main menu after /start."""
    labels = {
        "en": {
            "send": "💌 Send an Apology",
            "crush": "💖 Send a Crush",
            "inbox": "📬 My Inbox",
            "history": "📖 History",
            "settings": "⚙️ Settings",
            "help": "❓ Help",
        },
        "am": {
            "send": "💌 ይቅርታ ላክ",
            "crush": "💖 የፍቅር መልዕክት ላክ",
            "inbox": "📬 የደረሱኝ",
            "history": "📖 ታሪክ",
            "settings": "⚙️ ቅንብሮች",
            "help": "❓ እርዳታ",
        }
    }.get(lang, "en")

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(labels["send"], callback_data="menu_send")],
        [InlineKeyboardButton(labels["crush"], callback_data="menu_crush")],
        [InlineKeyboardButton(labels["inbox"], callback_data="menu_inbox")],
        [InlineKeyboardButton(labels["history"], callback_data="menu_history")],
        [InlineKeyboardButton(labels["settings"], callback_data="menu_settings")],
        [InlineKeyboardButton(labels["help"], callback_data="menu_help")],
    ])


def tone_keyboard(lang: str = "en", message_type: str = "apology") -> InlineKeyboardMarkup:
    """Tone selection during apology/crush composition."""
    if message_type == "crush":
        labels = {
            "en": ["🕶️ Secret Admirer", "🌹 Romantic", "✨ Flirty", "📜 Poetic", "💓 Direct"],
            "am": ["🕶️ ሚስጥራዊ አድናቂ", "🌹 የፍቅር", "✨ ፈገግታ", "📜 ስነ-ግጥማዊ", "💓 ግልጽ"]
        }.get(lang, "en")
        
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(labels[0], callback_data="tone_secret_admirer"),
                InlineKeyboardButton(labels[1], callback_data="tone_romantic"),
            ],
            [
                InlineKeyboardButton(labels[2], callback_data="tone_flirty"),
                InlineKeyboardButton(labels[3], callback_data="tone_poetic"),
            ],
            [
                InlineKeyboardButton(labels[4], callback_data="tone_direct"),
            ],
        ])

    labels = {
        "en": ["📜 Formal", "💔 Emotional", "🤝 Friendly", "🕊️ Deep Regret", "💌 Short & Simple"],
        "am": ["📜 መደበኛ (Formal)", "💔 ስሜታዊ (Emotional)", "🤝 የወዳጅነት (Friendly)", "🕊️ ጥልቅ ፀጸት", "💌 አጭር እና ቀላል"]
    }.get(lang, "en")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(labels[0], callback_data="tone_formal"),
            InlineKeyboardButton(labels[1], callback_data="tone_emotional"),
        ],
        [
            InlineKeyboardButton(labels[2], callback_data="tone_friendly"),
            InlineKeyboardButton(labels[3], callback_data="tone_deep_regret"),
        ],
        [
            InlineKeyboardButton(labels[4], callback_data="tone_short_simple"),
        ],
    ])


def anonymous_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Anonymous or identified toggle."""
    labels = {
        "en": ["🕶️ Anonymous", "👤 With my name"],
        "am": ["🕶️ ማንነትን ሳይገልጹ", "👤 በስሜ"]
    }.get(lang, "en")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(labels[0], callback_data="anon_yes"),
            InlineKeyboardButton(labels[1], callback_data="anon_no"),
        ],
    ])


def confirm_send_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Confirm / edit / cancel after preview."""
    labels = {
        "en": ["✅ Send", "✏️ Edit message", "🔄 Change tone", "❌ Cancel"],
        "am": ["✅ ላክ", "✏️ መልዕክት አስተካክል", "🔄 ቶን ቀይር", "❌ ሰርዝ"]
    }.get(lang, "en")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(labels[0], callback_data="confirm_send"),
            InlineKeyboardButton(labels[1], callback_data="confirm_edit"),
        ],
        [
            InlineKeyboardButton(labels[2], callback_data="confirm_tone"),
            InlineKeyboardButton(labels[3], callback_data="confirm_cancel"),
        ],
    ])


def ai_rewrite_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Offer AI rewriting."""
    labels = {
        "en": ["✨ Make it more sincere (AI)", "➡️ Keep as is"],
        "am": ["✨ ይበልጥ እውነተኛ አድርግ (AI)", "➡️ ይቆይ"]
    }.get(lang, "en")

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(labels[0], callback_data="ai_rewrite")],
        [InlineKeyboardButton(labels[1], callback_data="ai_skip")],
    ])


def settings_keyboard(
    receive_enabled: bool,
    allow_anon: bool,
    lang: str = "en"
) -> InlineKeyboardMarkup:
    """Settings panel."""
    # Basic toggle labels
    if lang == "am":
        recv_label = "✅ መቀበል: በርቷል" if receive_enabled else "❌ መቀበል: ጠፍቷል"
        anon_label = "✅ ማንነቱ ያልታወቀ: በርቷል" if allow_anon else "❌ ማንነቱ ያልታወቀ: ጠፍቷል"
        history_label = "🗑️ የውይይት ታሪክ ማጥፊያ"
        back_label = "🔙 ወደ ዋና ሜኑ"
    else:
        recv_label = "✅ Receiving: ON" if receive_enabled else "❌ Receiving: OFF"
        anon_label = "✅ Anonymous msgs: ON" if allow_anon else "❌ Anonymous msgs: OFF"
        history_label = "🗑️ Delete conversation history"
        back_label = "🔙 Back to menu"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(recv_label, callback_data="toggle_receive")],
        [InlineKeyboardButton(anon_label, callback_data="toggle_anon")],
        [InlineKeyboardButton(history_label, callback_data="delete_history")],
        [InlineKeyboardButton(back_label, callback_data="back_menu")],
    ])


def reveal_request_keyboard(apology_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Sent to original sender when identity reveal is requested."""
    labels = {
        "en": ["👤 Reveal my identity", "🕶️ Stay anonymous"],
        "am": ["👤 ማንነቴን ግለጽ", "🕶️ በምስጢር ይቆይ"]
    }.get(lang, "en")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(labels[0], callback_data=f"do_reveal_{apology_id}"),
            InlineKeyboardButton(labels[1], callback_data=f"stay_anon_{apology_id}"),
        ],
    ])


def report_reason_keyboard(apology_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Report reason selection."""
    labels = {
        "en": ["🚫 Spam", "😠 Harassment", "⚠️ Inappropriate", "🔪 Threats", "📝 Other"],
        "am": ["🚫 ስፓም", "😠 ትንኮሳ", "⚠️ ተገቢ ያልሆነ", "🔪 ማስፈራሪያ", "📝 ሌላ"]
    }.get(lang, "en")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(labels[0], callback_data=f"rr_spam_{apology_id}"),
            InlineKeyboardButton(labels[1], callback_data=f"rr_harassment_{apology_id}"),
        ],
        [
            InlineKeyboardButton(labels[2], callback_data=f"rr_inappropriate_{apology_id}"),
            InlineKeyboardButton(labels[3], callback_data=f"rr_threats_{apology_id}"),
        ],
        [
            InlineKeyboardButton(labels[4], callback_data=f"rr_other_{apology_id}"),
        ],
    ])
