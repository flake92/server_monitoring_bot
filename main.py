import asyncio
from aiogram import Bot, Dispatcher
from config.config import Config
from database.db_manager import DatabaseManager
from handlers import user_handlers, admin_handlers, monitoring_handlers
from services.monitoring import ServerMonitor
from services.notification import NotificationService
from services.cooldown import CooldownManager
from utils.logger import setup_logger

async def main():
    logger = setup_logger()
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(bot)

    db = DatabaseManager()
    await db.connect()

    cooldown_manager = CooldownManager()
    monitor = ServerMonitor(cooldown_manager)
    notification_service = NotificationService(bot)

    await monitor.start()

    # Регистрация обработчиков
    user_handlers.register_handlers(dp)
    admin_handlers.register_handlers(dp)
    monitoring_handlers.register_handlers(dp)

    async def monitoring_task():
        while True:
            await monitor.monitor_servers(db, notification_service)
            await notification_service.send_notifications(db)
            await asyncio.sleep(60)  # Проверка каждую минуту

    try:
        await asyncio.gather(
            dp.start_polling(),
            monitoring_task()
        )
    finally:
        await monitor.stop()
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())