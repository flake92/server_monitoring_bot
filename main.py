import logging
from aiogram import Bot, Dispatcher, executor
from dotenv import load_dotenv
import os
import asyncio
from handlers import user_handlers, admin_handlers, monitoring_handlers
from services.monitoring import start_monitoring
from config.config import Config
from utils.logger import setup_logger

# Настройка логирования
logger = setup_logger(__name__)

# Загрузка конфигурации
load_dotenv()
config = Config()

# Инициализация бота
bot = Bot(token=config.bot_token)
dp = Dispatcher(bot)

# Регистрация обработчиков
user_handlers.register_handlers(dp)
admin_handlers.register_handlers(dp)
monitoring_handlers.register_handlers(dp)

async def on_startup(_):
    logger.info("Starting bot")
    asyncio.create_task(start_monitoring(bot, config))

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")