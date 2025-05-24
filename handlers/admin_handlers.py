from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.config import Config
from database.db_manager import DBManager
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = Router()

async def admin_middleware(handler, event, data):
    config = Config.from_env()
    if event.from_user.id not in config.admin_ids:
        await event.reply("Доступ запрещён.")
        return
    return await handler(event, data)

router.message.outer_middleware(admin_middleware)
router.callback_query.outer_middleware(admin_middleware)

@router.message(Command("admin"))
async def admin_command(message: Message):
    logger.info(f"Received /admin from user {message.from_user.id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Модерация заявок", callback_data="moderate")],
        [InlineKeyboardButton(text="Список пользователей", callback_data="list_users")],
        [InlineKeyboardButton(text="Очистить уведомления", callback_data="clear_notifications")]
    ])
    await message.reply("Админ-панель:", reply_markup=keyboard)

@router.message(Command("reset_pending"))
async def reset_pending_command(message: Message):
    logger.info(f"Received /reset_pending from user {message.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        pending_users = await db.get_pending_users()
        if not pending_users:
            await message.reply("Нет пользователей с ожидающими заявками.")
            return
        for user in pending_users:
            await db.delete_user(user["id"])
            logger.info(f"Deleted pending user {user['id']}")
        await message.reply(f"Удалено {len(pending_users)} пользователей с ожидающими заявками.")

@router.callback_query(F.data == "moderate")
async def moderate_callback(callback: CallbackQuery):
    logger.info(f"Received moderate callback from admin {callback.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        pending_users = await db.get_pending_users()
        if not pending_users:
            await callback.message.reply("Нет заявок на модерацию.")
            return
        for user in pending_users:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{user['id']}")],
                [InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user['id']}")]
            ])
            await callback.message.reply(f"Пользователь: @{user['username']} (ID: {user['id']})", reply_markup=keyboard)

@router.callback_query(F.data.startswith("approve_"))
async def approve_user_callback(callback: CallbackQuery):
    logger.info(f"Received approve callback from admin {callback.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        user_id = int(callback.data.split("_")[1])
        user = await db.get_user(user_id)
        if not user:
            await callback.message.reply("Пользователь не найден.")
            return
        await db.update_user_status(user_id, "approved")
        await callback.message.reply(f"Пользователь @{user['username']} одобрен.")
        try:
            await callback.message.bot.send_message(user_id, "Ваша заявка одобрена!")
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

@router.callback_query(F.data.startswith("reject_"))
async def reject_user_callback(callback: CallbackQuery):
    logger.info(f"Received reject callback from admin {callback.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        user_id = int(callback.data.split("_")[1])
        user = await db.get_user(user_id)
        if not user:
            await callback.message.reply("Пользователь не найден.")
            return
        await db.delete_user(user_id)
        await callback.message.reply(f"Пользователь @{user['username']} отклонен.")
        try:
            await callback.message.bot.send_message(user_id, "Ваша заявка отклонена.")
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

@router.callback_query(F.data == "list_users")
async def list_users_callback(callback: CallbackQuery):
    logger.info(f"Received list_users callback from admin {callback.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        users = await db.get_approved_users()
        if not users:
            await callback.message.reply("Нет одобренных пользователей.")
            return
        response = "Список пользователей:\n"
        for user in users:
            response += f"ID: {user['id']}, @{user['username']}\n"
            servers = await db.get_user_servers(user["id"])
            if servers:
                response += "  Серверы:\n"
                for server in servers:
                    response += f"    {server['name']} ({server['address']}, {server['check_type']}): {server['status']}\n"
        await callback.message.reply(response)

@router.callback_query(F.data == "clear_notifications")
async def clear_notifications_callback(callback: CallbackQuery):
    logger.info(f"Received clear_notifications callback from admin {callback.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        await db.clear_notifications()
        await callback.message.reply("Уведомления очищены.")