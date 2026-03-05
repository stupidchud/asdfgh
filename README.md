# asdfgh
![Language](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Yet another advanced Discord bot written in Python using discord.py

# Setup

1. #### Python 3.8+ & sqlite3

   Required to run both the bot and API

2. #### Virtual environment

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. #### Install dependencies

   ```
   pip install -r requirements.txt
   ```

4. #### Configure environment

   Edit `config.py` to match your values, then create a `.env` in the project root:

   ```
   # Bot
   BOT_TOKEN=""               # Discord bot token
   LASTFM_API_KEY=""          # Last.fm API key

   # API
   DATABASE_URL=""            # Path to your sqlite db, e.g. data/sqlite/main.db
   JWT_SECRET=""              # openssl rand -hex 32
   BOT_API_KEY=""             # openssl rand -hex 32 — for internal bot <-> API calls

   # OAuth
   DISCORD_CLIENT_ID=""       # From Discord developer portal
   DISCORD_CLIENT_SECRET=""   # From Discord developer portal
   DISCORD_REDIRECT_URI=""    # e.g. http://localhost:8000/oauth/callback
   ```

5. #### Setup database

   Create the data directory then apply both schema files:

   ```
   mkdir -p data/sqlite

   sqlite3 data/sqlite/main.db < helpers/schema/tables.sql
   sqlite3 data/sqlite/main.db < helpers/schema/sessions.sql
   ```

# Running

### Bot

```
python3 run.py
```

### API

```
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger docs will be available at `http://localhost:8000/docs`

# Privacy Policy and Terms of Service

## Privacy Policy

asdfgh collects and stores server IDs, user IDs, and related data necessary for bot functionality. All data is stored locally and is not shared with third parties. Data may be deleted upon request.

## Terms of Service

This bot is provided as-is. By using this bot, you agree that the bot owner is not liable for any issues arising from its use. The bot owner reserves the right to modify or terminate service at any time.

# License

MIT
