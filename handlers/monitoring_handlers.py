from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config.config import Config
from database.db_manager import DBManager
from services.monitoring import MonitoringService
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = Router()

@router.message(Command("monitor"))
async def monitor_command(message: Message):
    logger.info(f"Received /monitor from user {message.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        async with MonitoringService(config) as monitoring:
            try:
                user = await db.get_user(message.from_user.id)
                if not user or user["status"] != "approved":
                    await message.reply("Вы не зарегистрированы или не одобрены.")
                    return
                servers = await db.get_user_servers(message.from_user.id)
                if not servers:
                    await message.reply("У вас нет серверов.")
                    return
                response = "Статус серверов:\n"
                for server in servers:
                    status = await monitoring.check_server(server)
                    await db.update_server_status(
                        server["id"],
                        "online" if status.is_online else "offline",
                        status.last_checked,
                        status.response_time,
                        status.error_message
                    )
                    status_emoji = "🟢" if status.is_online else "🔴"
                    response += f"{server['name']} ({server['address']}): {status_emoji}\n"
                await message.reply(response)
            except Exception as e:
                logger.error(f"Error in monitor_command: {e}")
                await message.reply("Произошла ошибка при проверке серверов.")