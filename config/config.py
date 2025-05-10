import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "server_monitoring")
    DB_USER = os.getenv("DB_USER", "monitor_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "secure_password")
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    COOLDOWN_PERIOD = 20  # seconds