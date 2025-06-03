from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Config:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    db_path: str = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'bot.db'))

config = Config()
