from bot import Bot

from os.path import join, dirname
from dotenv import load_dotenv

import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

load_dotenv(
    join(
        dirname(__file__), ".env"
    )
)

if __name__ == "__main__":
    bot = Bot()
    bot.run(token=os.environ.get("BOT_TOKEN")) #type: ignore
