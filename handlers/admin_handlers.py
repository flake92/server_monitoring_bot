from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import DBManager
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['admin'])
    async def admin_command(message: Message):
        logger.info(f"Received /admin from user {message.from_user.id}")
        try:
            config = Config()
            admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
            if not admin_ids:
                logger.error("No admin IDs configured in ADMIN_IDS")
                await message.reply("Ошибка: список администраторов пуст.")
                return
            if str(message.from_user.id) not in admin_ids:
                logger.warning(f"Access denied for user {message.from_user.id}")
                await message.reply("Доступ запрещён.")
                return
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Модерация заявок", callback_data="moderate"))
            keyboard.add(InlineKeyboardButton("Список пользователей", callback_data="list_users"))
            keyboard.add(InlineKeyboardButton("Очистить уведомления", callback_data="clear_notifications"))
            await message.reply("Админ-панель:", reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in admin_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.message_handler(commands=['reset_pending'])
    async def reset_pending_command(message: Message):
        logger.info(f"Received /reset_pending from user {message.from_user.id}")
        try:
            config = Config()
            admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
            if not admin_ids:
                logger.error("No admin IDs configured in ADMIN_IDS")
                await message.reply("Ошибка: список администраторов пуст.")
                return
            if str(message.from_user.id) not in admin_ids:
                logger.warning(f"Access denied for user {message.from_user.id}")
                await message.reply("Доступ запрещён.")
                return
            db = DBManager()
            pending_users = db.get_pending_users()
            if not pending_users:
                await message.reply("Нет пользователей с ожидающими заявками.")
                db.close()
                return
            for user in pending_users:
                db.delete_user(user.id)
                logger.info(f"Deleted pending user {user.id}")
            await message.reply(f"Удалено {len(pending_users)} пользователей с ожидающими заявками.")
            db.close()
        except Exception as e:
            logger.error(f"Error in reset_pending_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.callback_query_handler(lambda c: c.data == 'moderate')
    async def moderate_callback(callback: types.CallbackQuery):
        logger.info(f"Received moderate callback from admin {callback.from_user.id}")
        try:
            db = DBManager()
            pending_users = db.get_pending_users()
            logger.info(f"Found {len(pending_users)} pending users")
            if not pending_users:
                await callback.message.reply("Нет заявок на модерацию.")
                db.close()
                return
            for user in pending_users:
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("Одобрить", callback_data=f"approve_{user.id}"))
                keyboard.add(InlineKeyboardButton("Отклонить", callback_data=f"reject_{user.id}"))
                await callback.message.reply(f"Пользователь: @{user.username} (ID: {user.id})", reply_markup=keyboard)
            db.close()
        except Exception as e:
            logger.error(f"Error in moderate_callback: {e}")
            await callback.message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.callback_query_handler(lambda c: c.data.startswith('approve_'))
    async def approve_user_callback(callback: types.CallbackQuery):
        logger.info(f"Received approve callback from admin {callback.from_user.id}")
        try:
            user_id = int(callback.data.split('_')[1])
            db = DBManager()
            db.update_user_status(user_id, 'approved')
            user = db.get_user(user_id)
            await callback.message.reply(f"Пользователь @{user.username} одобрен.")
            try:
                await callback.message.bot.send_message(user_id, "Ваша заявка одобрена! Используйте /help для списка команд.")
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
            db.close()
        except Exception as e:
            logger.error(f"Error in approve_user_callback: {e}")
            await callback.message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.callback_query_handler(lambda c: c.data.startswith('reject_'))
    async def reject_user_callback(callback: types.CallbackQuery):
        logger.info(f"Received reject callback from admin {callback.from_user.id}")
        try:
            user_id = int(callback.data.split('_')[1])
            db = DBManager()
            db.delete_user(user_id)
            await callback.message.reply(f"Пользователь ID {user_id} отклонён и удалён.")
            db.close()
        except Exception as e:
            logger.error(f"Error in reject_user_callback: {e}")
            await callback.message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.callback_query_handler(lambda c: c.data == 'list_users')
    async def list_users_callback(callback: types.CallbackQuery):
        logger.info(f"Received list_users callback from admin {callback.from_user.id}")
        try:
            db = DBManager()
            users = db.get_approved_users()
            logger.info(f"Found {len(users)} approved users")
            if not users:
                await callback.message.reply("Нет одобренных пользователей.")
                db.close()
                return
            response = "Одобренные пользователи:\n"
            for user in users:
                response += f"ID: {user.id}, @{user.username}\n"
                servers = db.get_user_servers(user.id)
                if servers:
                    response += "  Серверы:\n"
                    for server in servers:
                        response += f"    {server.name} ({server.address}, {server.check_type}): {server.status}\n"
            await callback.message.reply(response)
            db.close()
        except Exception as e:
            logger.error(f"Error in list_users_callback: {e}")
            await callback.message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.callback_query_handler(lambda c: c.data == 'clear_notifications')
    async def clear_notifications_callback(callback: types.CallbackQuery):
        logger.info(f"Received clear_notifications callback from admin {callback.from_user.id}")
        try:
            db = DBManager()
            db.clear_notifications()
            await callback.message.reply("Очередь уведомлений очищена.")
            db.close()
        except Exception as e:
            logger.error(f"Error in clear_notifications_callback: {e}")
            await callback.message.reply("Произошла ошибка. Попробуйте позже.")