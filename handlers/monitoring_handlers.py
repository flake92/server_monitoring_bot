from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from database.db_manager import DatabaseManager
from services.monitoring import ServerMonitor

def register_handlers(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "check_status")
    async def check_status(callback: CallbackQuery, db: DatabaseManager, monitor: ServerMonitor):
        user = await db.get_user(callback.from_user.id)
        if not user or user.status != "approved":
            await callback.message.answer("Доступ запрещен или заявка не одобрена.")
            await callback.answer()
            return
        servers = await db.get_user_servers(callback.from_user.id)
        if not servers:
            await callback.message.answer("У вас нет добавленных серверов.")
            await callback.answer()
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
        await callback.message.answer(status_message)
        await callback.answer()