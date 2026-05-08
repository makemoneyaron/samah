# 🕊️ Samah Bot

> *A safe emotional bridge between people.*

Samah Bot is a Telegram bot that allows users to send heartfelt apologies, reconciliation messages, and forgiveness requests — **anonymously or with their identity**.

---

## ✨ Features

- **💌 Send Apologies** — Multi-step flow with tone selection, anonymity toggle, AI rewriting, and preview
- **📬 Inbox** — View received apologies with accept/reject/reply actions
- **💬 Reply System** — Threaded relay conversations through the bot
- **🕶️ Anonymous Mode** — Full anonymity with optional identity reveal requests
- **🔒 Safety** — Rate limiting, content moderation, blocking, and abuse reporting
- **🤖 AI Rewriting** — Optional OpenAI-powered apology refinement
- **👑 Admin Panel** — Stats, report management, user banning, broadcast messaging
- **⚙️ User Settings** — Control receiving, anonymity preferences, and history

## 📂 Project Structure

```
samahbot/
├── main.py                 # Entry point
├── config.py               # Environment-based configuration
├── requirements.txt        # Dependencies
├── handlers/
│   ├── start.py            # /start & onboarding
│   ├── help.py             # /help
│   ├── send_apology.py     # ConversationHandler for sending
│   ├── inbox.py            # /inbox — received messages
│   ├── history.py          # /history — sent messages
│   ├── settings.py         # /settings — user preferences
│   ├── recipient_actions.py # Accept, reject, reply, reveal, block, report
│   ├── blocklist.py        # /blocklist management
│   ├── report.py           # /report standalone flow
│   └── admin.py            # Admin commands
├── database/
│   ├── models.py           # SQLAlchemy ORM models
│   ├── session.py          # Async engine & session factory
│   └── queries.py          # CRUD query layer
├── services/
│   ├── formatter.py        # Apology formatting & templates
│   ├── delivery.py         # Message delivery & pending queue
│   ├── moderation.py       # Content moderation & validation
│   └── ai_rewriter.py      # Optional AI rewriting (OpenAI)
├── utils/
│   ├── keyboards.py        # Inline keyboard builders
│   ├── texts.py            # All user-facing strings
│   └── logging_setup.py    # Logging configuration
├── middlewares/
│   ├── auth.py             # User registration & ban check
│   └── rate_limiter.py     # Per-user rate limiting
├── Dockerfile              # Docker container config
├── Procfile                # Railway/Render process file
├── railway.json            # Railway deployment config
└── render.yaml             # Render deployment config
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-repo/samahbot.git
cd samahbot
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_IDS
```

**Required:**
- `BOT_TOKEN` — Get from [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS` — Your Telegram user ID (comma-separated for multiple)

**Optional:**
- `OPENAI_API_KEY` — Enable AI apology rewriting
- `WEBHOOK_URL` — Set for webhook mode (leave blank for polling)

### 3. Run

```bash
python main.py
```

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Open the main menu |
| `/send` | Send an apology |
| `/inbox` | View received messages |
| `/history` | View sent messages |
| `/settings` | Privacy & preferences |
| `/blocklist` | Manage blocked users |
| `/report` | Report abusive behaviour |
| `/help` | Show help |
| `/admin` | Admin dashboard (admins only) |

## 🚢 Deployment

### Railway
1. Push to GitHub
2. Connect repo to Railway
3. Set environment variables in Railway dashboard
4. Deploy

### Render
1. Push to GitHub
2. Create new Worker service on Render
3. Connect repo
4. Set environment variables
5. Deploy

### Docker
```bash
docker build -t samahbot .
docker run -d --env-file .env samahbot
```

## 🔐 Security

- Rate limiting (configurable per-hour limit + cooldown)
- Content moderation with blocked patterns
- User blocking system
- Abuse reporting with admin review
- Ban system for abusive users
- Input validation on all user inputs

## 📜 License

MIT

---

*Built with empathy. 🤍*
