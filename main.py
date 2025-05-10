import logging
from aiogram import Bot, Dispatcher, executor
from dotenv import load_dotenv
import os
from handlers import user_handlers, admin_handlers, monitoring_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Регистрация обработчиков
user_handlers.register_handlers(dp)
admin_handlers.register_handlers(dp)
monitoring_handlers.register_handlers(dp)

if __name__ == '__main__':
    logger.info("Starting bot")
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")