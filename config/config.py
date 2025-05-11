import os
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger(__name__)

load_dotenv()

class Config:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        if not self.bot_token:
            logger.error("BOT_TOKEN is not set in .env")
            raise ValueError("BOT_TOKEN is required")
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'server_monitoring')
        self.db_user = os.getenv('DB_USER', 'monitor_user')
        self.db_password = os.getenv('DB_PASSWORD')
        if not self.db_password:
            logger.error("DB_PASSWORD is not set in .env")
            raise ValueError("DB_PASSWORD is required")
        self.admin_ids = os.getenv('ADMIN_IDS', '')
        if not self.admin_ids:
            logger.warning("ADMIN_IDS is not set in .env, no administrators configured")
        self.monitoring_interval = 60  # Секунды
        self.cooldown_period = 20  # Секунды