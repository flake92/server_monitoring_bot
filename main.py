import asyncio
from aiogram import Bot, Dispatcher
from config.config import Config
from database.db_manager import DBManager
from utils.logger import setup_logger
from handlers import user_handlers, admin_handlers, monitoring_handlers
import logging

logger = logging.getLogger(__name__)

async def main():
    """Основная функция программы."""
    setup_logger()
    
    try:
        Config.validate()
        logger.info("Конфигурация проверена")

        db = DBManager()
        bot = Bot(token=Config.BOT_TOKEN)
        dp = Dispatcher()

        dp.include_router(user_handlers.router)
        dp.include_router(admin_handlers.router)

        dp["db"] = db

        asyncio.create_task(monitoring_handlers.monitor_servers(db, bot))

        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")