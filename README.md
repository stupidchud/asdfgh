# asdfgh

Yet another advanced Discord bot written in Python using discord.py

# Setup

1. #### Python 3 or higher & sqlite3

Required to run the bot

2. #### Set up virtual environment

Can be done through
```
python3 -m venv venv

source /venv/bin/activate
```

3. #### Install libraries

Through `pip install -r requirements.txt`

4. #### Setup configuration

Configure the `config.py` file to match your values, along with `.env`:

```
BOT_TOKEN=""        # Your discord bot token
LASTFM_API_KEY=""   # Your lastfm api key
```

5. #### Setup database

Do this through:

```
sqlite3 data/sqlite/main.db < helpers/schema/tables.sql
```

6. #### Running

Simply

```
python3 run.py
```

# Privacy Policy and Terms of Service

## Privacy Policy

asdfgh collects and stores server IDs, user IDs, and related data necessary for bot functionality. All data is stored locally and is not shared with third parties. Data may be deleted upon request.

## Terms of Service

This bot is provided as-is. By using this bot, you agree that the bot owner is not liable for any issues arising from its use. The bot owner reserves the right to modify or terminate service at any time.

# License

MIT