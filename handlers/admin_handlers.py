from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command
from database.db_manager import DatabaseManager
from config.config import Config

def get_admin_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Список заявок", callback_data="list_pending"))
    keyboard.add(InlineKeyboardButton(text="Все пользователи", callback_data="list_users"))
    keyboard.add(InlineKeyboardButton(text="Очистить очередь", callback_data="clear_queue"))
    return keyboard

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=["admin"])
    async def admin_command(message: Message, db: DatabaseManager):
        if message.from_user.id not in Config.ADMIN_IDS:
            await message.answer("Доступ запрещен.")
            return
        await message.answer("Админ-панель:", reply_markup=get_admin_menu())

    @dp.callback_query_handler(lambda c: c.data == "list_pending")
    async def list_pending_users(callback: CallbackQuery, db: DatabaseManager):
        if callback.from_user.id not in Config.ADMIN_IDS:
            return
        pending_users = await db.get_pending_users()
        if not pending_users:
            await callback.message.answer("Нет заявок на модерацию.")
            return
        for user in pending_users:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{user.user_id}"))
            keyboard.add(InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user.user_id}"))
            await callback.message.answer(
                f"ID: {user.user_id}\n"
                f"Username: @{user.username}\n"
                f"Имя: {user.first_name} {user.last_name}",
                reply_markup=keyboard
            )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "list_users")
    async def list_all_users(callback: CallbackQuery, db: DatabaseManager):
        if callback.from_user.id not in Config.ADMIN_IDS:
            return
        users = await db.get_approved_users()
        if not users:
            await callback.message.answer("Нет одобренных пользователей.")
            return
        for user in users:
            servers = await db.get_user_servers(user.user_id)
            servers_info = "\n".join([f" - {s.name} ({s.address}, {s.check_type})" for s in servers]) if servers else "Нет серверов"
            await callback.message.answer(
                f"ID: {user.user_id}\n"
                f"Username: @{user.username}\n"
                f"Имя: {user.first_name} {user.last_name}\n"
                f"Сервера:\n{servers_info}"
            )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "clear_queue")
    async def clear_queue(callback: CallbackQuery, db: DatabaseManager):
        if callback.from_user.id not in Config.ADMIN_IDS:
            return
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM notifications WHERE is_sent = FALSE")
        await callback.message.answer("Очередь уведомлений очищена.")
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data.startswith("approve_"))
    async def approve_user(callback: CallbackQuery, db: DatabaseManager):
        if callback.from_user.id not in Config.ADMIN_IDS:
            return
        user_id = int(callback.data.split("_")[1])
        await db.update_user_status(user_id, "approved")
        await callback.message.answer(f"Пользователь {user_id} одобрен.")
        await callback.bot.send_message(user_id, "Ваша заявка одобрена! Бот доступен.")
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data.startswith("reject_"))
    async def reject_user(callback: CallbackQuery, db: DatabaseManager):
        if callback.from_user.id not in Config.ADMIN_IDS:
            return
        user_id = int(callback.data.split("_")[1])
        await db.update_user_status(user_id, "rejected")
        await callback.message.answer(f"Пользователь {user_id} отклонен.")
        await callback.bot.send_message(user_id, "Ваша заявка отклонена.")
        await callback.answer()