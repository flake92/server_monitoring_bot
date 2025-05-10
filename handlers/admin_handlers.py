from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config.config import Config
from database.db_manager import DBManager
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("admin"))
async def admin_command(message: Message, db: DBManager) -> None:
    """Обработчик команды /admin."""
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    pending_users = db.get_pending_users()
    if pending_users:
        response = "Заявки на модерацию:\n" + "\n".join(
            f"ID: {u.id}, Username: @{u.username}"
            for u in pending_users
        )
        await message.answer(response + "\n\nДля одобрения: /approve <user_id>\nДля отклонения: /reject <user_id>")
    else:
        await message.answer("Нет заявок на модерацию.")

@router.message(Command("approve"))
async def approve_command(message: Message, db: DBManager) -> None:
    """Обработчик команды /approve."""
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет доступа.")
        return
    
    try:
        user_id = int(message.text.split()[1])
        user = db.get_user(user_id)
        if user:
            db.update_user_status(user_id, "approved")
            await message.bot.send_message(user_id, "Ваша заявка одобрена! Используйте /add_server для добавления сервера.")
            await message.answer(f"Пользователь {user_id} одобрен.")
        else:
            await message.answer("Пользователь не найден.")
    except (IndexError, ValueError):
        await message.answer("Использование: /approve <user_id>")

@router.message(Command("reject"))
async def reject_command(message: Message, db: DBManager) -> None:
    """Обработчик команды /reject."""
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет доступа.")
        return
    
    try:
        user_id = int(message.text.split()[1])
        user = db.get_user(user_id)
        if user:
            db.update_user_status(user_id, "rejected")
            await message.bot.send_message(user_id, "Ваша заявка отклонена. Обратитесь к администратору.")
            await message.answer(f"Пользователь {user_id} отклонен.")
        else:
            await message.answer("Пользователь не найден.")
    except (IndexError, ValueError):
        await message.answer("Использование: /reject <user_id>")