from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from typing import Dict, Optional
import logging
import re

from database.db_manager import DBManager
from database.models import User, Server, NotificationSettings
from utils.logger import setup_logger
from config import Config

# Initialize router and logger
router = Router()
logger = setup_logger(__name__)

# Global state for tracking expected user inputs
expected_id_input: Dict[str, str] = {}

# Keyboard builders
def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Мои серверы")
    builder.button(text="Добавить сервер")
    builder.button(text="Проверить серверы")
    builder.button(text="Помощь")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_admin_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Список пользователей")
    builder.button(text="Одобрить пользователя")
    builder.button(text="Удалить пользователя")
    builder.button(text="Тест уведомлений")
    builder.button(text="Назад")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Helper functions
def is_valid_server_address(address: str) -> bool:
    pattern = r'^[\w.-]+(?::\d+)?$'
    return bool(re.match(pattern, address))

def is_admin(user_id: int) -> bool:
    config = Config()
    admin_ids = [int(id.strip()) for id in config.admin_ids.split(',') if id.strip()]
    return user_id in admin_ids

def validate_port(port: str) -> bool:
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False

def parse_server_address(address: str) -> tuple[str, int]:
    if ':' in address:
        host, port = address.rsplit(':', 1)
        if not validate_port(port):
            raise ValueError("Invalid port number")
        return host, int(port)
    return address, 80  # Default to port 80 if not specified

# Command handlers
@router.message(Command("start"))
async def start_command(message: Message):
    logger.info(f"Received /start from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        
        if user is None:
            # Add new user with pending status
            db.add_user(
                user_id=message.from_user.id,
                username=message.from_user.username or "Unknown",
                status="pending"
            )
            await message.reply(
                "Добро пожаловать! Ваша заявка на регистрацию отправлена администратору.",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
            )
        elif user.status == "pending":
            await message.reply(
                "Ваша заявка все еще находится на рассмотрении у администратора.",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
            )
        elif user.status == "approved":
            await message.reply(
                "Добро пожаловать в систему мониторинга серверов!",
                reply_markup=get_main_menu()
            )
            if is_admin(message.from_user.id):
                await message.reply(
                    "Вы вошли как администратор. Используйте /admin для доступа к панели администратора."
                )
        else:
            await message.reply(
                "Ваш аккаунт заблокирован. Обратитесь к администратору.",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
            )
        db.close()
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply(
            "Произошла ошибка при регистрации. Попробуйте позже.",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
        )

@router.message(Command("help"))
async def help_command(message: Message):
    logger.info(f"Received /help from user {message.from_user.id}")
    help_text = """Доступные команды:

/start - Начать работу с ботом
/help - Показать это сообщение
/admin - Панель администратора (только для админов)

Кнопки меню:
- Мои серверы - просмотр и управление вашими серверами
- Добавить сервер - добавить новый сервер для мониторинга
- Проверить серверы - проверка состояния всех ваших серверов
- Редактировать сервер - изменить настройки сервера
- Удалить сервер - удалить сервер из мониторинга"""
    await message.reply(help_text)

@router.message(Command("admin"))
async def admin_command(message: Message):
    logger.info(f"Received /admin from user {message.from_user.id}")
    if not is_admin(message.from_user.id):
        await message.reply("У вас нет доступа к панели администратора.")
        return
    
    await message.reply(
        "Панель администратора:",
        reply_markup=get_admin_menu()
    )

@router.message(Command("add_server"))
async def add_server_command(message: Message):
    logger.info(f"Received /add_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
            db.close()
            return

        expected_id_input[str(message.from_user.id)] = 'add_server'
        await message.reply(
            "Введите адрес сервера в формате: IP:порт (например, 192.168.1.1:80)",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in add_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")

# Command handlers
@router.message(Command("start"))
async def start_command(message: Message):
    logger.info(f"Received /start from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        
        if user is None:
            # Add new user with pending status
            db.add_user(
                user_id=message.from_user.id,
                username=message.from_user.username or "Unknown",
                status="pending"
            )
            await message.reply(
                "Добро пожаловать! Ваша заявка на регистрацию отправлена администратору.",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
            )
        elif user.status == "pending":
            await message.reply(
                "Ваша заявка все еще находится на рассмотрении у администратора.",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
            )
        elif user.status == "approved":
            await message.reply(
                "Добро пожаловать в систему мониторинга серверов!",
                reply_markup=get_main_menu()
            )
            if is_admin(message.from_user.id):
                await message.reply(
                    "Вы вошли как администратор. Используйте /admin для доступа к панели администратора."
                )
        else:
            await message.reply(
                "Ваш аккаунт заблокирован. Обратитесь к администратору.",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
            )
        db.close()
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply(
            "Произошла ошибка при регистрации. Попробуйте позже.",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
        )
        logger.info(f"Received /start from user {message.from_user.id}")
        try:
            db = DBManager()
            user = db.get_user(message.from_user.id)
            config = Config()
            admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
            logger.info(f"Parsed admin_ids: {admin_ids}")
            is_admin = str(message.from_user.id) in admin_ids

            if user is None:
                logger.info(f"Adding new user {message.from_user.id} with status {'approved' if is_admin else 'pending'}")
                status = 'approved' if is_admin else 'pending'
                db.add_user(message.from_user.id, message.from_user.username or "unknown", status)
                if is_admin:
                    logger.info(f"User {message.from_user.id} registered as admin with approved status")
                    await message.reply(
                        "Добро пожаловать, администратор! Используйте /admin для доступа к панели.",
                        reply_markup=get_main_menu()
                    )
                else:
                    logger.info(f"Attempting to notify admins about new user {message.from_user.id}")
                    if admin_ids:
                        for admin_id in admin_ids:
                            try:
                                await message.bot.send_message(
                                    admin_id,
                                    f"Новая заявка на регистрацию:\n"
                                    f"Пользователь: @{message.from_user.username or 'unknown'} (ID: {message.from_user.id})"
                                )
                                logger.info(f"Successfully notified admin {admin_id} about new user {message.from_user.id}")
                            except Exception as e:
                                logger.error(f"Failed to notify admin {admin_id}: {e}")
                                for fallback_admin_id in [aid for aid in admin_ids if aid != admin_id]:
                                    try:
                                        await message.bot.send_message(
                                            fallback_admin_id,
                                            f"Ошибка: не удалось уведомить админа {admin_id} о новой заявке (ID: {message.from_user.id}). Причина: {str(e)}"
                                        )
                                        logger.info(f"Notified fallback admin {fallback_admin_id} about notification failure")
                                    except Exception as fe:
                                        logger.error(f"Failed to notify fallback admin {fallback_admin_id}: {fe}")
                    else:
                        logger.error("No admin IDs configured in ADMIN_IDS, cannot send notifications")
                    await message.reply("Заявка на регистрацию отправлена. Ожидайте одобрения администратора.")
            else:
                logger.info(f"User {message.from_user.id} already exists with status {user.status}")
                if user.status == 'pending' and is_admin:
                    logger.info(f"Updating user {message.from_user.id} from pending to approved")
                    db.update_user_status(message.from_user.id, 'approved')
                    logger.info(f"Updated user {message.from_user.id} to approved as admin")
                    await message.reply(
                        "Добро пожаловать, администратор! Ваш статус обновлён. Используйте /admin для доступа к панели.",
                        reply_markup=get_main_menu()
                    )
                elif user.status == 'pending':
                    await message.reply("Ваша заявка на рассмотрении.")
                elif user.status == 'approved':
                    welcome_msg = "Добро пожаловать в бот мониторинга серверов!" if not is_admin else \
                                 "Добро пожаловать, администратор! Используйте /admin для доступа к панели."
                    await message.reply(welcome_msg, reply_markup=get_main_menu())
            db.close()
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

@router.message(Command("help"))
async def help_command(message: Message):
    logger.info(f"Received /help from user {message.from_user.id}")
    await message.reply(
        "Доступные команды:\n"
        "/start - Запустить бот\n"
        "/help - Показать справку\n"
        "/add_server - Добавить сервер\n"
        "/list_servers - Показать список серверов\n"
        "/edit_server - Редактировать сервер\n"
        "/delete_server - Удалить сервер\n"
        "/check_servers - Проверить статус серверов\n"
        "/admin - Админ-панель (для администраторов)\n"
        "/debug_notify - Проверить уведомления (для администраторов)\n"
        "/list_pending_users - Показать пользователей с ожидающими заявками (для администраторов)\n"
        "/delete_user - Удалить пользователя (для администраторов)\n"
        "/approve_user - Одобрить заявку пользователя (для администраторов)\n"
        "/resend_notification - Повторно отправить уведомления о заявках (для администраторов)"
    )

@router.message(Command("admin"))
async def handle_menu_commands(message: Message):
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.")
            db.close()
            return

        if message.text == "Проверить серверы":
            servers = db.get_user_servers(message.from_user.id)
            if not servers:
                await message.reply("У вас нет добавленных серверов.")
            else:
                status_text = "Статус серверов:\n\n"
                for server in servers:
                    status = "\u2705" if server.status == "up" else "\u274c"
                    response_time = f"{server.response_time:.2f}ms" if server.response_time else "N/A"
                    status_text += f"{status} {server.name} - {response_time}\n"
                    if server.error_message:
                        status_text += f"\u26a0\ufe0f {server.error_message}\n"
                await message.reply(status_text)

        elif message.text == "Мои сервера":
            servers = db.get_user_servers(message.from_user.id)
            if not servers:
                await message.reply("У вас нет добавленных серверов.")
            else:
                servers_text = "Ваши серверы:\n\n"
                for server in servers:
                    servers_text += f"ID: {server.id}\n"
                    servers_text += f"Имя: {server.name}\n"
                    servers_text += f"Адрес: {server.address}:{server.port}\n"
                    servers_text += "---\n"
                await message.reply(servers_text)

        elif message.text == "Добавить сервер":
            await add_server_command(message)

        elif message.text == "Помощь":
            await help_command(message)

        db.close()
    except Exception as e:
        logger.error(f"Error in handle_menu_commands: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")
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
        await message.reply("Админ-панель:", reply_markup=get_admin_menu())
    except Exception as e:
        logger.error(f"Error in admin_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")

@router.message(Command("debug_notify"))
async def debug_notify_command(message: Message):
    logger.info(f"Received /debug_notify from user {message.from_user.id}")
    try:
        config = Config()
        admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
        logger.info(f"Parsed admin_ids for debug_notify: {admin_ids}")
        if not admin_ids:
            logger.error("No admin IDs configured in ADMIN_IDS")
            await message.reply("Ошибка: список администраторов пуст.")
            return
        if str(message.from_user.id) not in admin_ids:
            logger.warning(f"Access denied for user {message.from_user.id}")
            await message.reply("Доступ запрещён.")
            return
        for admin_id in admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"Тестовое уведомление от бота:\n"
                    f"Отправлено от админа ID: {message.from_user.id}\n"
                    f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                logger.info(f"Sent test notification to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to send test notification to admin {admin_id}: {e}")
                await message.reply(f"Ошибка при отправке тестового уведомления админу {admin_id}: {str(e)}")
        await message.reply("Тестовые уведомления отправлены всем администраторам.")
    except Exception as e:
        logger.error(f"Error in debug_notify_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")

async def list_pending_users_command(message: Message):
    logger.info(f"Received /list_pending_users from user {message.from_user.id}")
    try:
        config = Config()
        admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
        logger.info(f"Parsed admin_ids for list_pending_users: {admin_ids}")
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
            await message.reply("Нет пользователей с ожидающими заявками.", reply_markup=get_admin_menu())
        else:
            response = "Пользователи с ожидающими заявками:\n"
            for user in pending_users:
                response += f"ID: {user.id}, Username: @{user.username or 'unknown'}, Status: {user.status}\n"
            await message.reply(response, reply_markup=get_admin_menu())
        db.close()
    except Exception as e:
        logger.error(f"Error in list_pending_users_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())

@router.message(Command("delete_user"))
async def delete_user_command(message: Message):
    logger.info(f"Received /delete_user from user {message.from_user.id}")
    try:
        config = Config()
        admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
        logger.info(f"Parsed admin_ids for delete_user: {admin_ids}")
        if not admin_ids:
            logger.error("No admin IDs configured in ADMIN_IDS")
            await message.reply("Ошибка: список администраторов пуст.")
            return
        if str(message.from_user.id) not in admin_ids:
            logger.warning(f"Access denied for user {message.from_user.id}")
            await message.reply("Доступ запрещён.")
            return
        args = message.get_args()
        if not args:
            await message.reply("Укажите ID пользователя. Пример: /delete_user 123456789")
            return
        try:
            user_id = int(args.strip())
        except ValueError:
            await message.reply("ID пользователя должен быть числом.")
            return
        db = DBManager()
        user = db.get_user(user_id)
        if user is None:
            await message.reply(f"Пользователь с ID {user_id} не найден.", reply_markup=get_admin_menu())
        else:
            db.delete_user(user_id)
            await message.reply(f"Пользователь с ID {user_id} удалён.", reply_markup=get_admin_menu())
        db.close()
    except Exception as e:
        logger.error(f"Error in delete_user_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())

@router.message(Command("approve_user"))
async def approve_user_command(message: Message):
    logger.info(f"Received /approve_user from user {message.from_user.id}")
    try:
        config = Config()
        admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
        logger.info(f"Parsed admin_ids for approve_user: {admin_ids}")
        if not admin_ids:
            logger.error("No admin IDs configured in ADMIN_IDS")
            await message.reply("Ошибка: список администраторов пуст.")
            return
        if str(message.from_user.id) not in admin_ids:
            logger.warning(f"Access denied for user {message.from_user.id}")
            await message.reply("Доступ запрещён.")
            return
        args = message.get_args()
        if not args:
            await message.reply("Укажите ID пользователя. Пример: /approve_user 123456789")
            return
        try:
            user_id = int(args.strip())
        except ValueError:
            await message.reply("ID пользователя должен быть числом.")
            return
        db = DBManager()
        user = db.get_user(user_id)
        if user is None:
            await message.reply(f"Пользователь с ID {user_id} не найден.", reply_markup=get_admin_menu())
        elif user.status == 'approved':
            await message.reply(f"Пользователь с ID {user_id} уже одобрен.", reply_markup=get_admin_menu())
        else:
            db.update_user_status(user_id, 'approved')
            try:
                await message.bot.send_message(
                    user_id,
                    "Ваша заявка одобрена! Добро пожаловать в бот мониторинга серверов!",
                    reply_markup=get_main_menu()
                )
                logger.info(f"Sent approval notification to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to notify user {user_id} about approval: {e}")
                await message.reply(
                    f"Статус пользователя {user_id} обновлён, но не удалось отправить уведомление: {str(e)}",
                    reply_markup=get_admin_menu()
                )
            await message.reply(f"Пользователь с ID {user_id} одобрен.", reply_markup=get_admin_menu())
        db.close()
    except Exception as e:
        logger.error(f"Error in approve_user_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())

@router.message(Command("resend_notification"))
async def resend_notification_command(message: Message):
    logger.info(f"Received /resend_notification from user {message.from_user.id}")
    try:
        config = Config()
        admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
        logger.info(f"Parsed admin_ids for resend_notification: {admin_ids}")
        if not admin_ids:
            logger.error("No admin IDs configured in ADMIN_IDS")
            await message.reply("Ошибка: список администраторов пуст.")
            return
        if str(message.from_user.id) not in admin_ids:
            logger.warning(f"Access denied for user {message.from_user.id}")
            await message.reply("Доступ запрещён.")
            return
        db = DBManager()
        last_notification = db.get_last_notification_time()
        current_time = datetime.utcnow()
        cooldown_seconds = 300  # 5 минут
        if last_notification and (current_time - last_notification).total_seconds() < cooldown_seconds:
            remaining_seconds = int(cooldown_seconds - (current_time - last_notification).total_seconds())
            await message.reply(
                f"Подождите {remaining_seconds} секунд перед повторной отправкой уведомлений.",
                reply_markup=get_admin_menu()
            )
            db.close()
            return
        pending_users = db.get_pending_users()
        if not pending_users:
            await message.reply("Нет пользователей с ожидающими заявками.", reply_markup=get_admin_menu())
            db.close()
            return
        for user in pending_users:
            for admin_id in admin_ids:
                try:
                    await message.bot.send_message(
                        admin_id,
                        f"Новая заявка на регистрацию:\n"
                        f"Пользователь: @{user.username or 'unknown'} (ID: {user.id})"
                    )
                    logger.info(f"Successfully notified admin {admin_id} about user {user.id}")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
        db.update_last_notification_time(datetime.utcnow())
        await message.reply("Уведомления о заявках отправлены администраторам.", reply_markup=get_admin_menu())
        db.close()
    except Exception as e:
        logger.error(f"Error in resend_notification_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())

@router.message(Command("add_server"))
async def add_server_command(message: Message):
    logger.info(f"Received /add_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
            db.close()
            return

        expected_id_input[str(message.from_user.id)] = 'add_server'
        await message.reply(
            "Введите адрес сервера в формате: IP:порт (например, 192.168.1.1:80)",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in add_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")

    await handle_menu_commands(message)
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
            db.close()
            return

        expected_id_input[str(message.from_user.id)] = 'add_server'
        await message.reply(
            "Введите адрес сервера в формате: IP:порт (например, 192.168.1.1:80)",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in add_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")
@router.message(F.text)
async def process_add_server(message: Message):
    """Обработчик добавления нового сервера.

    Args:
        message (Message): Входящее сообщение с адресом сервера
    """
    logger.info(f"Processing server data from user {message.from_user.id}")
    user_id_str = str(message.from_user.id)

    if message.text == "Назад":
        expected_id_input.pop(user_id_str, None)
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return

    try:
        if message.from_user.id not in expected_id_input or expected_id_input[message.from_user.id] != 'add_server':
            return
        del expected_id_input[message.from_user.id]

        address = message.text.strip()
        if not re.match(r'^(?:\d{1,3}\.){3}\d{1,3}:\d+$|^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:\d+$', address):
            await message.reply(
                "Неверный формат адреса. Используйте формат IP:порт или домен:порт\n"
                "Пример: 192.168.1.1:80 или example.com:80",
                reply_markup=get_main_menu()
            )
            return

        host, port = address.split(':')
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            await message.reply(
                "Порт должен быть числом от 1 до 65535",
                reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            server_id = db.add_server(
                user_id=message.from_user.id,
                name=f"Server {host}:{port}",
                address=address,
                check_type='http'
            )
            await message.reply(
                f"Сервер {host}:{port} успешно добавлен (ID: {server_id})",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logger.error(f"Failed to add server to database: {e}")
            await message.reply(
                "Не удалось добавить сервер. Возможно, он уже существует.",
                reply_markup=get_main_menu()
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in process_add_server: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu()
        )

@router.message(Command("list_servers"))
async def list_servers_command(message: Message):
    logger.info(f"Received /list_servers from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
        else:
            response = "Ваши серверы:\n"
            for server in servers:
                status_emoji = "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
                response += f"{status_emoji} {server.name} (ID: {server.id})\n"
                response += f"   Адрес: {server.address}\n"
                response += f"   Тип проверки: {server.check_type}\n"
                response += f"   Статус: {server.status}\n\n"
            await message.reply(response, reply_markup=get_main_menu())
        db.close()
    except Exception as e:
        logger.error(f"Error in list_servers_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())

@router.message(Command("edit_server"))
async def edit_server_command(message: Message):
    logger.info(f"Received /edit_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            db.close()
            return

        response = "Выберите сервер для редактирования:\n\n"
        for server in servers:
            status_emoji = "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            response += f"{status_emoji} {server.name} (ID: {server.id})\n"
            response += f"   Адрес: {server.address}\n"
            response += f"   Тип проверки: {server.check_type}\n\n"

        expected_id_input[message.from_user.id] = 'edit_server'
        await message.reply(
            response + "Введите ID сервера для редактирования:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in edit_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())

@router.message(F.text)
async def process_edit_server(message: Message):
    logger.info(f"Processing edit server data from user {message.from_user.id}")
    try:
        if message.from_user.id not in expected_id_input or expected_id_input[message.from_user.id] != 'edit_server':
            return
        del expected_id_input[message.from_user.id]

        try:
            server_id = int(message.text.strip())
        except ValueError:
            await message.reply(
                "Неверный формат ID. ID должен быть числом.",
                reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            server = next((s for s in db.get_user_servers(message.from_user.id) if s.id == server_id), None)
            if server is None:
                await message.reply(
                    f"Сервер с ID {server_id} не найден или не принадлежит вам.",
                    reply_markup=get_main_menu()
                )
                db.close()
                return

            expected_id_input[message.from_user.id] = f'edit_server_{server_id}'
            await message.reply(
                f"Выбран сервер: {server.name}\n"
                f"Текущий адрес: {server.address}\n"
                f"Текущий тип проверки: {server.check_type}\n\n"
                f"Введите новый адрес сервера в формате IP:порт или домен:порт\n"
                f"Пример: 192.168.1.1:80 или example.com:80"
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            await message.reply(
                "Не удалось получить информацию о сервере.",
                reply_markup=get_main_menu()
            )
            db.close()
    except Exception as e:
        logger.error(f"Error in process_edit_server: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu()
        )

@router.message(F.text)
async def process_edit_server_address(message: Message):
    logger.info(f"Processing edit server address from user {message.from_user.id}")
    try:
        if message.from_user.id not in expected_id_input or not expected_id_input[message.from_user.id].startswith('edit_server_'):
            return

        server_id = int(expected_id_input[message.from_user.id].split('_')[2])
        del expected_id_input[message.from_user.id]

        address = message.text.strip()
        if not re.match(r'^(?:\d{1,3}\.){3}\d{1,3}:\d+$|^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:\d+$', address):
            await message.reply(
                "Неверный формат адреса. Используйте формат IP:порт или домен:порт\n"
                "Пример: 192.168.1.1:80 или example.com:80",
                reply_markup=get_main_menu()
            )
            return

        host, port = address.split(':')
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            await message.reply(
                "Порт должен быть числом от 1 до 65535",
                reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            server = next((s for s in db.get_user_servers(message.from_user.id) if s.id == server_id), None)
            if server is None:
                await message.reply(
                    f"Сервер с ID {server_id} не найден или не принадлежит вам.",
                    reply_markup=get_main_menu()
                )
                db.close()
                return

            db.update_server(
                server_id=server_id,
                name=f"Server {host}:{port}",
                address=address,
                check_type='http'
            )
            await message.reply(
                f"Сервер успешно обновлён:\n"
                f"Новый адрес: {address}",
                reply_markup=get_main_menu()
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to update server: {e}")
            await message.reply(
                "Не удалось обновить сервер. Возможно, адрес уже используется.",
                reply_markup=get_main_menu()
            )
            db.close()
    except Exception as e:
        logger.error(f"Error in process_edit_server_address: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu()
        )

@router.message(Command("delete_server"))
@router.message(Command("delete_server"))
async def delete_server_command(message: Message):
    logger.info(f"Received /delete_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            db.close()
            return

        response = "Выберите сервер для удаления:\n\n"
        for server in servers:
            status_emoji = "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            response += f"{status_emoji} {server.name} (ID: {server.id})\n"
            response += f"   Адрес: {server.address}\n"
            response += f"   Тип проверки: {server.check_type}\n\n"

        expected_id_input[message.from_user.id] = 'delete_server'
        await message.reply(
            response + "Введите ID сервера для удаления:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in delete_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())

@router.message(F.text)
async def process_delete_server(message: Message):
    logger.info(f"Processing delete server from user {message.from_user.id}")
    try:
        if message.from_user.id not in expected_id_input or expected_id_input[message.from_user.id] != 'delete_server':
            return
        del expected_id_input[message.from_user.id]

        try:
            server_id = int(message.text.strip())
        except ValueError:
            await message.reply(
                "ИД сервера должен быть числом.",
                reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            server = next((s for s in db.get_user_servers(message.from_user.id) if s.id == server_id), None)
            if server is None:
                await message.reply(
                    f"Сервер с ID {server_id} не найден или не принадлежит вам.",
                    reply_markup=get_main_menu()
                )
                db.close()
                return

            db.delete_server(server_id)
            await message.reply(
                f"Сервер {server.name} (ID: {server_id}) успешно удалён.",
                reply_markup=get_main_menu()
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to delete server: {e}")
            await message.reply(
                "Не удалось удалить сервер.",
                reply_markup=get_main_menu()
            )
            db.close()
    except Exception as e:
        logger.error(f"Error in process_delete_server: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu()
        )

@router.message(Command("check_servers"))
async def check_servers_command(message: Message):
    logger.info(f"Received /check_servers from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != 'approved':
            await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            db.close()
            return

        response = "Ваши серверы:\n\n"
        for server in servers:
            status_emoji = "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            response += f"{status_emoji} {server.name} (ID: {server.id})\n"
            response += f"   Адрес: {server.address}\n"
            response += f"   Тип проверки: {server.check_type}\n"
            response += f"   Статус: {server.status}\n\n"

        expected_id_input[message.from_user.id] = 'check_server'
        await message.reply(
            response + "Введите ID сервера для проверки:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in check_servers_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())

@router.message(F.text)
async def process_check_server(message: Message):
    logger.info(f"Processing server check from user {message.from_user.id}")
    try:
        if message.from_user.id not in expected_id_input or expected_id_input[message.from_user.id] != 'check_server':
            return
        del expected_id_input[message.from_user.id]

        try:
            server_id = int(message.text.strip())
        except ValueError:
            await message.reply(
                "ИД сервера должен быть числом.",
                reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            server = next((s for s in db.get_user_servers(message.from_user.id) if s.id == server_id), None)
            if server is None:
                await message.reply(
                    f"Сервер с ID {server_id} не найден или не принадлежит вам.",
                    reply_markup=get_main_menu()
                )
                db.close()
                return

            status_emoji = "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            await message.reply(
                f"Статус сервера:\n"
                f"{status_emoji} {server.name} (ID: {server.id})\n"
                f"   Адрес: {server.address}\n"
                f"   Тип проверки: {server.check_type}\n"
                f"   Статус: {server.status}",
                reply_markup=get_main_menu()
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to check server: {e}")
            await message.reply(
                "Не удалось проверить сервер.",
                reply_markup=get_main_menu()
            )
            db.close()
    except Exception as e:
        logger.error(f"Error in process_check_server: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu()
        )

@router.message(F.text)
async def text_menu_handler(message: Message):
    """Обработчик текстовых команд меню.

    Args:
        message (Message): Входящее сообщение от пользователя
    """
    logger.info(f"Received text menu command from user {message.from_user.id}: {message.text}")
    try:
        config = Config()
        admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
        is_admin = str(message.from_user.id) in admin_ids
        user_id_str = str(message.from_user.id)

        # Обработка числовых ID для админских команд
        if is_admin and message.text.strip().isdigit() and user_id_str in expected_id_input:
            await process_delete_user_id(message)
            return

        # Обработка общих команд меню
        menu_commands = {
            "Назад": lambda: message.reply("Возвращение в главное меню.", reply_markup=get_main_menu()),
            "Помощь": help_command,
            "Администратор": admin_command,
            "Список серверов": list_servers_command,
            "Добавить сервер": add_server_command,
            "Редактировать сервер": edit_server_command,
            "Удалить сервер": delete_server_command,
            "Проверить серверы": check_servers_command
        }

        # Обработка админских команд
        admin_commands = {
            "Список пользователей": list_pending_users_command,
            "Удалить пользователя": delete_user_command,
            "Одобрить пользователя": approve_user_command,
            "Переотправить уведомление": resend_notification_command,
            "Повторно отправить уведомления": resend_notification_command,
            "Тест уведомлений": debug_notify_command
        }

        # Проверка и выполнение общих команд
        if message.text in menu_commands:
            await menu_commands[message.text](message)
            return

        # Проверка и выполнение админских команд
        if is_admin and message.text in admin_commands:
            await admin_commands[message.text](message)
            return

        # Если команда не найдена
        await message.reply(
            "Неизвестная команда. Воспользуйтесь кнопками меню.",
            reply_markup=get_main_menu()
        )

    except Exception as e:
        logger.error(f"Error in text_menu_handler: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_menu()
        )