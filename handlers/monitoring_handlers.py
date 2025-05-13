from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db_manager import DBManager
from services.monitoring import check_server
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = Router()


@router.message(Command("monitor"))
async def monitor_command(message: Message):
    logger.info(f"Received /monitor from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != "approved":
            await message.reply("Вы не зарегистрированы или не одобрены.")
            db.close()
            return
        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.")
            db.close()
            return
        response = "Статус серверов:\n"
        for server in servers:
            status = await check_server(server)
            db.update_server_status(server.id, status, server.last_checked)
            response += f"{server.name} ({server.address}): {status}\n"
        await message.reply(response)
        db.close()
    except Exception as e:
        logger.error(f"Error in monitor_command: {e}")
        await message.reply("Произошла ошибка при проверке серверов.")
