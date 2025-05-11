import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config.config import Config
from handlers import user_handlers, admin_handlers, monitoring_handlers

# Временный логгер для диагностики
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/deployer/server_monitoring_bot/debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Starting bot initialization")
        config = Config()
        logger.info("Config loaded successfully")
        
        logger.info(f"BOT_TOKEN: {'<hidden>' if config.bot_token else 'MISSING'}")
        logger.info(f"ADMIN_IDS: {config.admin_ids}")
        
        bot = Bot(token=config.bot_token)
        logger.info("Bot initialized")
        
        dp = Dispatcher(bot)
        logger.info("Dispatcher initialized")
        
        user_handlers.register_handlers(dp)
        admin_handlers.register_handlers(dp)
        monitoring_handlers.register_handlers(dp)
        logger.info("Handlers registered")
        
        logger.info("Starting polling")
        await dp.start_polling()
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main loop failed: {str(e)}", exc_info=True)
        sys.exit(1)