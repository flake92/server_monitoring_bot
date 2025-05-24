import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.sqlalchemy import SQLAlchemyStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine

from config.config import Config
from handlers import admin_handlers, monitoring_handlers, user_handlers
from services.monitoring import schedule_monitoring_tasks

# Ensure timezone is set to UTC
os.environ["TZ"] = "UTC"

# Setup logging with rotation
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("logs/bot.log", maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

async def main():
    try:
        config = Config.from_env()
        
        # Initialize database engine for storage
        db_url = (
            f"postgresql+asyncpg://{config.database.user}:{config.database.password}@"
            f"{config.database.host}:{config.database.port}/{config.database.name}"
        )
        engine = create_async_engine(db_url, echo=False)
        
        # Initialize bot and dispatcher
        bot = Bot(token=config.bot_token)
        storage = SQLAlchemyStorage(engine=engine)
        dp = Dispatcher(storage=storage)
        
        # Register handlers
        dp.include_routers(
            user_handlers.router,
            admin_handlers.router,
            monitoring_handlers.router,
        )
        
        # Initialize scheduler
        scheduler = AsyncIOScheduler(timezone="UTC")
        await schedule_monitoring_tasks(scheduler, bot, config)
        scheduler.start()
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}", exc_info=True)
        raise
    finally:
        if 'scheduler' in locals():
            scheduler.shutdown()
        if 'storage' in locals():
            await storage.close()
        if 'engine' in locals():
            await engine.dispose()
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())