from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database.db_manager import DatabaseManager
from services.monitoring import ServerMonitor

router = Router()

@router.message(Command("status"))
async def check_status(message: Message, db: DatabaseManager, monitor: ServerMonitor):
    user = await db.get_user(message.from_user.id)
    if not user or user.status != "approved":
        await message.answer("Доступ запрещен или заявка не одобрена.")
        return
    servers = await db.get_user_servers(message.from_user.id)
    if not servers:
        await message.answer("У вас нет добавленных серверов.")
        return
    status_message = "Статус ваших серверов:\n\n"
    for server in servers:
        is_available = await monitor.check_server(server)
        status_message += (
            f"Сервер: {server.name}\n"
            f"Адрес: {server.address}\n"
            f"Тип: {server.check_type}\n"
            f"Статус: {'Доступен' if is_available else 'Недоступен'}\n\n"
        )
    await message.answer(status_message)