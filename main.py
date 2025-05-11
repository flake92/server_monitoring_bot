import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import CommandStart
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config.config import Config
from handlers import user_handlers, admin_handlers, monitoring_handlers
from services.monitoring import schedule_monitoring_tasks

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'bot_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting middleware
class RateLimiter:
    def __init__(self):
        self.rates = {}

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        if user_id:
            now = datetime.now().timestamp()
            if user_id in self.rates:
                last_time = self.rates[user_id]
                if now - last_time < 1:  # 1 second cooldown
                    await event.answer("Пожалуйста, подождите перед следующей командой.")
                    return
            self.rates[user_id] = now
        return await handler(event, data)

async def main():
    try:
        logger.info("Starting bot initialization")
        config = Config()
        logger.info("Config loaded successfully")
        
        if not config.bot_token:
            raise ValueError("Bot token is missing!")
        
        logger.info(f"BOT_TOKEN: {'<hidden>' if config.bot_token else 'MISSING'}")
        logger.info(f"ADMIN_IDS: {config.admin_ids}")
        
        # Initialize bot and dispatcher
        bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Add rate limiting
        dp.message.middleware(RateLimiter())
        
        # Initialize scheduler
        scheduler = AsyncIOScheduler(timezone="UTC")
        
        # Register handlers
        user_handlers.register_handlers(dp)
        admin_handlers.register_handlers(dp)
        monitoring_handlers.register_handlers(dp)
        logger.info("Handlers registered")
        
        # Schedule monitoring tasks
        await schedule_monitoring_tasks(scheduler, bot)
        scheduler.start()
        
        logger.info("Starting bot")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
        raise
    finally:
        if 'bot' in locals():
            await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Main loop failed: {str(e)}", exc_info=True)
        sys.exit(1)