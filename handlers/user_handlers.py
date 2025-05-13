import re
from datetime import datetime
from enum import Enum
from typing import Dict

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import Config
from database.db_manager import DBManager
from utils.logger import setup_logger

# region Constants
class UserState(Enum):
    ADD_SERVER = "add_server"
    DELETE_USER = "delete_user"

EMOJI = {
    "SUCCESS": "✅",
    "ERROR": "❌",
    "PENDING": "⏳",
    "LOCKED": "🔒",
    "BACK": "🔙",
    "ONLINE": "🟢",
    "OFFLINE": "🔴",
    "SETTINGS": "⚙️",
    "HELP": "📚",
    "LIST": "📝",
    "EMPTY": "📭",
    "STATS": "📊",
    "GLOBE": "🌐",
    "BIN": "🗑",
    "WAVE": "👋",
    "UNLOCK": "🔓",
    "WARNING": "⚠️",
    "DENIED": "🚫"
}
# endregion

router = Router()
logger = setup_logger(__name__)
expected_id_input: Dict[str, UserState] = {}
expected_server_edit: Dict[str, int] = {}


# Keyboard builders
def get_main_menu() -> ReplyKeyboardMarkup:
    """Build and return the main menu keyboard markup.
    
    Returns:
        ReplyKeyboardMarkup: The main menu keyboard with common actions
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="Мои серверы")
    builder.button(text="Добавить сервер")
    builder.button(text="Проверить серверы")
    builder.button(text="Помощь")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Build and return the admin menu keyboard markup.
    
    Returns:
        ReplyKeyboardMarkup: The admin menu keyboard with administrative actions
    """
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
    pattern = r"^[\w.-]+(?::\d+)?$"
    return bool(re.match(pattern, address))


def is_admin(user_id: int) -> bool:
    config = Config()
    admin_ids = [int(id.strip()) for id in config.admin_ids.split(",") if id.strip()]
    return user_id in admin_ids


def validate_port(port: str) -> bool:
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False


def parse_server_address(address: str) -> tuple[str, int]:
    """Parse server address string into host and port.
    
    Args:
        address (str): Server address in format 'host:port' or just 'host'
        
    Returns:
        tuple[str, int]: Tuple containing host and port
        
    Raises:
        ValueError: If port is invalid
    """
    if ":" in address:
        host, port = address.rsplit(":", 1)
        if not validate_port(port):
            raise ValueError("Invalid port")
        return host, int(port)
    return address, 80  # Default to port 80 if not specified


# Command handlers
@router.message(Command("start"))
async def start_command(message: Message):
    logger.info(f"Received /start from user {message.from_user.id}")
    try:
        config = Config()
        db = DBManager()
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"
        admin_ids = [id.strip() for id in config.admin_ids.split(",") if id.strip()] if config.admin_ids else []
        is_admin_user = str(user_id) in admin_ids

        user = await db.get_user(user_id)
        if not user:
            status = "approved" if is_admin_user else "pending"
            await db.add_user(user_id, username, status)
            if is_admin_user:
                await message.reply(f"{EMOJI['WAVE']} Добро пожаловать, администратор!", reply_markup=get_main_menu())
            else:
                if admin_ids:
                    for admin_id in admin_ids:
                        await message.bot.send_message(admin_id, f"{EMOJI['LIST']} Новая заявка: @{username} (ID: {user_id})")
                await message.reply(f"{EMOJI['SUCCESS']} Заявка отправлена на одобрение")
            return

        status = user.get("status")
        if status == "pending" and is_admin_user:
            await db.update_user_status(user_id, "approved")
            await message.reply(f"{EMOJI['UNLOCK']} Ваш статус обновлён!", reply_markup=get_main_menu())
        elif status == "pending":
            await message.reply(f"{EMOJI['PENDING']} Заявка на рассмотрении")
        elif status == "approved":
            await message.reply(f"{EMOJI['WAVE']} Добро пожаловать!", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")
    finally:
        db.close()


@router.message(Command("help"))
async def help_command(message: Message):
    logger.info(f"Received /help from user {message.from_user.id}")
    help_text = (
        "📋 Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/add_server - Добавить новый сервер\n"
        "/list_servers - Показать список серверов\n"
        "/check_servers - Проверить состояние серверов\n"
        "/admin - Панель администратора (только для админов)"
    )
    await message.reply(help_text)


@router.message(Command("admin"))
async def admin_command(message: Message):
    logger.info(f"Received /admin from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply(f"{EMOJI['DENIED']} Доступ запрещён")
            return

        await message.reply(f"{EMOJI['SETTINGS']} Панель администратора:", reply_markup=get_admin_menu())
    except Exception as e:
        logger.error(f"Error in admin_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")


@router.message(Command("add_server"))
async def add_server_command(message: Message):
    logger.info(f"Received /add_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = await db.get_user(message.from_user.id)

        if not user or not user["is_approved"]:
            await message.reply(
                "У вас нет прав для добавления серверов. Пожалуйста, дождитесь одобрения."
            )
            return

        keyboard = ReplyKeyboardBuilder()
        keyboard.button(text="Назад")
        keyboard.adjust(1)

        await message.reply(
            "Введите адрес сервера в формате: example.com или example.com:80",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
        expected_id_input[str(message.from_user.id)] = UserState.ADD_SERVER
    except Exception as e:
        logger.error(f"Error in add_server_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")
    finally:
        db.close()
    help_text = (
        "📋 Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/add_server - Добавить новый сервер\n"
        "/list_servers - Показать список серверов\n"
        "/edit_server - Редактировать сервер\n"
        "/delete_server - Удалить сервер\n"
        "/check_servers - Проверить статус серверов\n"
        "/admin - Админ-панель (для администраторов)"
    )
    await message.reply(help_text)


@router.message(Command("admin"))
async def handle_admin_menu(message: Message):
    """Handle admin menu commands.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /admin from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к панели администратора")
            return

        keyboard = get_admin_menu()
        await message.reply("Панель администратора:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in handle_admin_menu: {e}")
        await message.reply("Ошибка. Попробуйте позже.")


@router.message(Command("debug_notify"))
async def debug_notify_command(message: Message):
    """Handle debug notify command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /debug_notify from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        # Отправляем тестовое уведомление
        await message.reply("Отправляю тестовое уведомление...")
        
        # Здесь можно добавить логику отправки тестового уведомления
        
        await message.reply(f"{EMOJI['SUCCESS']} Тестовое уведомление отправлено")
    except Exception as e:
        logger.error(f"Error in debug_notify_command: {e}")
        await message.reply(f"{EMOJI['ERROR']} Ошибка при обработке запроса")


@router.message(Command("list_pending_users"))
async def list_pending_users_command(message: Message):
    """Handle list pending users command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /list_pending_users from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        db = DBManager()
        pending_users = await db.get_pending_users()

        if not pending_users:
            await message.reply(f"{EMOJI['EMPTY']} Нет ожидающих заявок")
            return

        users_text = "Пользователи с ожидающими заявками:\n\n"
        for user in pending_users:
            users_text += (
                f"ID: {user.id}\n"
                f"Имя: {user.username}\n"
                f"Дата регистрации: {user.registration_date}\n"
                "---\n"
            )

        await message.reply(users_text)
    except Exception as e:
        logger.error(f"Error in list_pending_users_command: {e}")
        await message.reply("Ошибка при получении списка пользователей")
    finally:
        db.close()


@router.message(Command("delete_user"))
async def delete_user_command(message: Message):
    """Handle delete user command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /delete_user from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        await message.reply("Введите ID пользователя для удаления:")
        expected_id_input[str(message.from_user.id)] = UserState.DELETE_USER
    except Exception as e:
        logger.error(f"Error in delete_user_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")



@router.message(Command("approve_user"))
async def approve_user_command(message: Message):
    """Handle approve user command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /approve_user from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        await message.reply("Введите ID пользователя для одобрения:")
        expected_id_input[str(message.from_user.id)] = "approve_user"
    except Exception as e:
        logger.error(f"Error in approve_user_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")


@router.message(Command("resend_notification"))
async def resend_notification_command(message: Message):
    """Handle resend notification command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /resend_notification from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        db = DBManager()
        pending_users = await db.get_pending_users()

        if not pending_users:
            await message.reply(f"{EMOJI['EMPTY']} Нет ожидающих заявок")
            return
            await message.reply(response, reply_markup=get_admin_menu())
        db.close()
    except Exception as e:
        logger.error(f"Error in list_pending_users_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())


@router.message(Command("delete_user"))
async def delete_user_command(message: Message):
    """Обработчик команды удаления пользователя.

    Args:
        message (Message): Входящее сообщение
    """
    logger.info(f"Received /delete_user from user {message.from_user.id}")
    try:
        expected_id_input[str(message.from_user.id)] = UserState.DELETE_USER
        await message.reply(
            "Введите ID пользователя для удаления:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
            ),
        )
    except Exception as e:
        logger.error(f"Error in delete_user_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())


@router.message(F.text)
async def process_delete_user_id(message: Message):
    """Обработчик удаления пользователя по ID.

    Args:
        message (Message): Входящее сообщение с ID пользователя
    """
    logger.info(f"Processing delete user ID from user {message.from_user.id}: {message.text}")
    user_id_str = str(message.from_user.id)

    if message.text == "Назад":
        expected_id_input.pop(user_id_str, None)
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return

    try:
        if user_id_str not in expected_id_input or expected_id_input[user_id_str] != UserState.DELETE_USER:
            return

        config = Config()
        admin_ids = (
            [id.strip() for id in config.admin_ids.split(",") if id.strip()]
            if config.admin_ids
            else []
        )
        logger.info(f"Parsed admin_ids for delete_user: {admin_ids}")

        if not admin_ids:
            logger.error("No admin IDs configured in ADMIN_IDS")
            await message.reply("Ошибка: список администратов пуст.")
            return

        if user_id_str not in admin_ids:
            logger.warning(f"Access denied for user {message.from_user.id}")
            await message.reply("Доступ запрещён.")
            return

        try:
            user_id = int(message.text.strip())
        except ValueError:
            await message.reply("ИД пользователя должен быть числом.")
            return

        db = DBManager()
        user = await db.get_user(user_id)

        if user is None:
            await message.reply(
                f"Пользователь с ID {user_id} не найден.", reply_markup=get_admin_menu()
            )
            return

        await db.delete_user(user_id)
        await message.reply(
            f"Пользователь с ID {user_id} удалён.", reply_markup=get_admin_menu()
        )

        try:
            await message.bot.send_message(
                user_id,
                "Ваша заявка отклонена. Вы можете попробовать зарегистрироваться позже."
            )
            logger.info(f"Sent rejection notification to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send rejection notification to user {user_id}: {e}")
            await message.reply(
                f"Пользователь удалён, но не удалось отправить уведомление: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Error in process_delete_user_id: {e}")
        await message.reply("Ошибка при удалении пользователя")
    finally:
        db.close()


@router.message(Command("list_servers"))
async def list_servers_command(message: Message):
    """Handle list servers command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /list_servers from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        db = DBManager()
        servers = await db.get_servers()

        if not servers:
            await message.reply("Список серверов пуст")
            return

        response = "Список серверов:\n\n"
        for server in servers:
            response += (
                f"ID: {server.id}\n"
                f"Адрес: {server.address}\n"
                f"Порт: {server.port}\n"
                f"Статус: {server.status}\n"
                "---\n"
            )

        await message.reply(response)
    except Exception as e:
        logger.error(f"Error in list_servers_command: {e}")
        await message.reply("Ошибка при получении списка серверов")
    finally:
        db.close()


@router.message(Command("edit_server"))
async def edit_server_command(message: Message):
    """Handle edit server command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /edit_server from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        await message.reply("Введите ID сервера для редактирования:")
        expected_server_input[str(message.from_user.id)] = "edit_server"
    except Exception as e:
        logger.error(f"Error in edit_server_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")


@router.message(Command("delete_server"))
async def delete_server_command(message: Message):
    """Handle delete server command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /delete_server from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        await message.reply("Введите ID сервера для удаления:")
        expected_server_input[str(message.from_user.id)] = "delete_server"
    except Exception as e:
        logger.error(f"Error in delete_server_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")


@router.message(Command("check_servers"))
async def check_servers_command(message: Message):
    """Handle check servers command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /check_servers from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к этой команде")
            return

        db = DBManager()
        servers = await db.get_servers()

        if not servers:
            await message.reply("Список серверов пуст")
            return

        for server in servers:
            try:
                status = await check_server_status(server.address, server.port)
                await db.update_server_status(server.id, status)
                await message.reply(
                    f"Статус сервера {server.address}:{server.port}: {status}"
                )
            except Exception as e:
                logger.error(f"Error checking server {server.id}: {e}")
                await message.reply(
                    f"Ошибка при проверке сервера {server.address}:{server.port}: {str(e)}"
                )
    except Exception as e:
        logger.error(f"Error in check_servers_command: {e}")
        await message.reply("Ошибка при проверке серверов")
    finally:
        db.close()


@router.message(F.text)
async def process_server_input(message: Message):
    """Process server input.

    Args:
        message (Message): Message from user
    """
    user_id_str = str(message.from_user.id)
    if user_id_str not in expected_server_input:
        return

    action = expected_server_input[user_id_str]
    del expected_server_input[user_id_str]

    try:
        server_id = int(message.text.strip())
    except ValueError:
        await message.reply(f"{EMOJI['LOCKED']} Требуется одобрение аккаунта")
        return

    try:
        db = DBManager()
        server = await db.get_server(server_id)

        if server is None:
            await message.reply(
                f"Сервер с ID {server_id} не найден."
            )
            return

        if action == "edit_server":
            await message.reply(
                "Введите новый адрес сервера в формате IP:Порт или Домен:Порт"
            )
            expected_server_edit[user_id_str] = server_id
        elif action == "delete_server":
            await db.delete_server(server_id)
            await message.reply(
                f"Сервер с ID {server_id} удалён."
            )
    except Exception as e:
        logger.error(f"Error in process_server_input: {e}")
        await message.reply("Ошибка. Попробуйте позже.")
    finally:
        db.close()


@router.message(F.text)
async def process_server_edit(message: Message):
    """Process server edit input.

    Args:
        message (Message): Message from user
    """
    user_id_str = str(message.from_user.id)
    if user_id_str not in expected_server_edit:
        return

    server_id = expected_server_edit[user_id_str]
    del expected_server_edit[user_id_str]

    try:
        address = message.text.strip()
        if not is_valid_server_address(address):
            await message.reply("Некорректный адрес сервера. Используйте формат IP:Порт или Домен:Порт")
            return

        host, port = parse_server_address(address)
        if not validate_port(port):
            await message.reply("Некорректный порт. Порт должен быть числом от 1 до 65535")
            return

        db = DBManager()
        await db.update_server(server_id, host, int(port))
        await message.reply(
            f"Сервер с ID {server_id} обновлён. Новый адрес: {host}:{port}"
        )
    except Exception as e:
        logger.error(f"Error in process_server_edit: {e}")
        await message.reply("Ошибка. Попробуйте позже.")
    finally:
        db.close()


@router.message(Command("help"))
async def help_command(message: Message):
    """Handle help command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /help from user {message.from_user.id}")
    try:
        help_text = (
            "Список доступных команд:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            "/admin - Панель администратора\n"
        )

        if is_admin(message.from_user.id):
            help_text += (
                "\nКоманды администратора:\n"
                "/list_pending_users - Список пользователей с ожидающими заявками\n"
                "/approve_user - Одобрить пользователя\n"
                "/delete_user - Удалить пользователя\n"
                "/add_server - Добавить сервер\n"
                "/list_servers - Список серверов\n"
                "/edit_server - Редактировать сервер\n"
                "/delete_server - Удалить сервер\n"
                "/check_servers - Проверить статус серверов\n"
                "/debug_notify - Отправить тестовое уведомление\n"
            )

        await message.reply(help_text)
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")


@router.message(Command("start"))
async def start_command(message: Message):
    """Handle start command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /start from user {message.from_user.id}")
    try:
        db = DBManager()
        user = await db.get_user(message.from_user.id)

        if user is None:
            username = message.from_user.username or "Unknown"
            await db.add_user(message.from_user.id, username, "pending")
            await message.reply(
                "Ваша заявка на регистрацию принята. Ожидайте одобрения администратора."
            )
            logger.info(f"New user registration: {message.from_user.id} ({username})")
        elif user.status == "pending":
            await message.reply(
                "Ваша заявка находится на рассмотрении. Ожидайте одобрения администратора."
            )
        elif user.status == "approved":
            await message.reply(
                "Добро пожаловать в бот мониторинга серверов!",
                reply_markup=get_main_menu(),
            )
        else:
            await message.reply(
                "Ваш аккаунт заблокирован. Обратитесь к администратору."
            )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")
    finally:
        db.close()


@router.message(Command("admin"))
async def admin_command(message: Message):
    """Handle admin command.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Received /admin from user {message.from_user.id}")
    try:
        if not is_admin(message.from_user.id):
            await message.reply("У вас нет прав для доступа к панели администратора")
            return

        await message.reply("Панель администратора:", reply_markup=get_admin_menu())
    except Exception as e:
        logger.error(f"Error in admin_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")


@router.message(Command("add_server"))
async def add_server_command(message: Message):
    logger.info(f"Received /add_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)

        if user is None or user.status != "approved":
            await message.reply(
                "Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu()
            )
            db.close()
            return

        expected_id_input[str(message.from_user.id)] = UserState.ADD_SERVER
        await message.reply(
            "Введите адрес сервера в формате: IP:порт (например, 192.168.1.1:80)",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
            ),
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in add_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")


async def add_server_command(message: Message):
    """Обработчик команды добавления сервера.

    Args:
        message (Message): Входящее сообщение
    """
    logger.info(f"Received /add_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)

        if user is None or user.status != "approved":
            await message.reply(
                "Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu()
            )
            db.close()
            return

        expected_id_input[str(message.from_user.id)] = UserState.ADD_SERVER
        await message.reply(
            "Введите адрес сервера в формате: IP:порт (например, 192.168.1.1:80)",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
            ),
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in add_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")


@router.message(F.text)
async def text_menu_handler(message: Message):
    logger.info(f"Received text message from user {message.from_user.id}: {message.text}")
    try:
        user_id = str(message.from_user.id)
        text = message.text

        if text == "Назад":
            expected_id_input.pop(user_id, None)
            await message.reply("Возврат в меню.", reply_markup=get_main_menu())
            return

        # Обработка состояний
        if user_id in expected_id_input:
            match expected_id_input[user_id]:
                case UserState.ADD_SERVER:
                    await process_add_server(message)
                case UserState.DELETE_USER:
                    await process_delete_user(message)
                case _:
                    logger.warning(f"Unknown state: {expected_id_input[user_id]}")
                    await message.reply(f"{EMOJI['WARNING']} Неизвестная команда")
        host, port = address.split(":")
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            await message.reply(
                "Порт должен быть числом от 1 до 65535", reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            server_id = db.add_server(
                user_id=message.from_user.id,
                name=f"Server {host}:{port}",
                address=address,
                check_type="http",
            )
            await message.reply(
                f"Сервер {host}:{port} успешно добавлен (ID: {server_id})",
                reply_markup=get_main_menu(),
            )
        except Exception as e:
            logger.error(f"Failed to add server to database: {e}")
            await message.reply(
                "Не удалось добавить сервер. Возможно, он уже существует.",
                reply_markup=get_main_menu(),
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in process_add_server: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.", reply_markup=get_main_menu()
        )


@router.message(Command("list_servers"))
async def list_servers_command(message: Message):
    logger.info(f"Received /list_servers from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != "approved":
            await message.reply(
                "Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu()
            )
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
        else:
            response = "Ваши серверы:\n"
            for server in servers:
                status_emoji = (
                    "🟢"
                    if server.status == "online"
                    else "🔴" if server.status == "offline" else "⚪️"
                )
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
        if user is None or user.status != "approved":
            await message.reply(
                "Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu()
            )
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            db.close()
            return

        response = "Выберите сервер для редактирования:\n\n"
        for server in servers:
            status_emoji = (
                "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            )
            response += f"{status_emoji} {server.name} (ID: {server.id})\n"
            response += f"   Адрес: {server.address}\n"
            response += f"   Тип проверки: {server.check_type}\n\n"

        expected_id_input[message.from_user.id] = "edit_server"
        await message.reply(
            response + "Введите ID сервера для редактирования:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in edit_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())


@router.message(F.text)
async def process_edit_server(message: Message):
    logger.info(f"Processing edit server data from user {message.from_user.id}")
    try:
        if (
            message.from_user.id not in expected_id_input
            or expected_id_input[message.from_user.id] != "edit_server"
        ):
            return
        del expected_id_input[message.from_user.id]

        try:
            server_id = int(message.text.strip())
        except ValueError:
            await message.reply(
                "Неверный формат ID. ID должен быть числом.", reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            server = next(
                (s for s in db.get_user_servers(message.from_user.id) if s.id == server_id), None
            )
            if server is None:
                await message.reply(
                    f"Сервер с ID {server_id} не найден или не принадлежит вам.",
                    reply_markup=get_main_menu(),
                )
                db.close()
                return

            expected_server_edit[message.from_user.id] = server_id
            await message.reply(
                f"Выбран сервер: {server.name}\n"
                f"Текущий адрес: {server.address}\n"
                f"Текущий тип проверки: {server.check_type}\n\n"
                f"Введите новый адрес сервера в формате IP:порт или домен:порт\n"
                f"Пример: 192.168.1.1:80 или example.com:80",
                reply_markup=types.ReplyKeyboardRemove()
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            await message.reply(
                "Не удалось получить информацию о сервере.", reply_markup=get_main_menu()
            )
            db.close()
    except Exception as e:
        logger.error(f"Error in process_edit_server: {e}")
        await message.reply(
            "Ошибка. Попробуйте позже.",
            reply_markup=get_main_menu()
        )


@router.message(F.text)
async def process_server_edit(message: Message):
    """Process server edit input.

    Args:
        message (Message): Message from user
    """
    logger.info(f"Processing server edit data from user {message.from_user.id}")
    try:
        if message.from_user.id not in expected_server_edit:
            return

        server_id = expected_server_edit[message.from_user.id]
        del expected_server_edit[message.from_user.id]

        address = message.text.strip()
        if not is_valid_server_address(address):
            await message.reply(
                "Некорректный адрес сервера. Используйте формат IP:Порт или Домен:Порт",
                reply_markup=get_main_menu()
            )
            return

        host, port = parse_server_address(address)
        if not validate_port(port):
            await message.reply(
                "Некорректный порт. Порт должен быть числом от 1 до 65535",
                reply_markup=get_main_menu()
            )
            return

        db = DBManager()
        try:
            await db.update_server(server_id, host, int(port))
            await message.reply(
                f"Сервер с ID {server_id} обновлён. Новый адрес: {host}:{port}",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logger.error(f"Failed to update server: {e}")
            await message.reply(
                "Не удалось обновить сервер.",
                reply_markup=get_main_menu()
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in process_server_edit: {e}")
        await message.reply(
            "Ошибка. Попробуйте позже.",
            reply_markup=get_main_menu()
        )


@router.message(Command("delete_server"))
async def delete_server_command(message: Message):
    logger.info(f"Received /delete_server from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != "approved":
            await message.reply(
                "Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu()
            )
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            db.close()
            return

        response = "Выберите сервер для удаления:\n\n"
        for server in servers:
            status_emoji = (
                "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            )
            response += f"{status_emoji} {server.name} (ID: {server.id})\n"
            response += f"   Адрес: {server.address}\n"
            response += f"   Тип проверки: {server.check_type}\n\n"

        expected_id_input[message.from_user.id] = "delete_server"
        await message.reply(
            response + "Введите ID сервера для удаления:", reply_markup=types.ReplyKeyboardRemove()
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in delete_server_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())


@router.message(F.text)
async def process_delete_server(message: Message):
    logger.info(f"Processing delete server from user {message.from_user.id}")
    try:
        if (
            message.from_user.id not in expected_id_input
            or expected_id_input[message.from_user.id] != "delete_server"
        ):
            return
        del expected_id_input[message.from_user.id]

        try:
            server_id = int(message.text.strip())
        except ValueError:
            await message.reply("ИД сервера должен быть числом.", reply_markup=get_main_menu())
            return

        db = DBManager()
        try:
            server = next(
                (s for s in db.get_user_servers(message.from_user.id) if s.id == server_id), None
            )
            if server is None:
                await message.reply(
                    f"Сервер с ID {server_id} не найден или не принадлежит вам.",
                    reply_markup=get_main_menu(),
                )
                db.close()
                return

            db.delete_server(server_id)
            await message.reply(
                f"Сервер {server.name} (ID: {server_id}) успешно удалён.",
                reply_markup=get_main_menu(),
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to delete server: {e}")
            await message.reply("Не удалось удалить сервер.", reply_markup=get_main_menu())
            db.close()
    except Exception as e:
        logger.error(f"Error in process_delete_server: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.", reply_markup=get_main_menu()
        )


@router.message(Command("check_servers"))
async def check_servers_command(message: Message):
    logger.info(f"Received /check_servers from user {message.from_user.id}")
    try:
        db = DBManager()
        user = db.get_user(message.from_user.id)
        if user is None or user.status != "approved":
            await message.reply(
                "Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu()
            )
            db.close()
            return

        servers = db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            db.close()
            return

        response = "Ваши серверы:\n\n"
        for server in servers:
            status_emoji = (
                "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            )
            response += f"{status_emoji} {server.name} (ID: {server.id})\n"
            response += f"   Адрес: {server.address}\n"
            response += f"   Тип проверки: {server.check_type}\n"
            response += f"   Статус: {server.status}\n\n"

        expected_id_input[message.from_user.id] = "check_server"
        await message.reply(
            response + "Введите ID сервера для проверки:", reply_markup=types.ReplyKeyboardRemove()
        )
        db.close()
    except Exception as e:
        logger.error(f"Error in check_servers_command: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())


@router.message(F.text)
async def process_check_server(message: Message):
    logger.info(f"Processing server check from user {message.from_user.id}")
    try:
        if (
            message.from_user.id not in expected_id_input
            or expected_id_input[message.from_user.id] != "check_server"
        ):
            return
        del expected_id_input[message.from_user.id]

        try:
            server_id = int(message.text.strip())
        except ValueError:
            await message.reply("ИД сервера должен быть числом.", reply_markup=get_main_menu())
            return

        db = DBManager()
        try:
            server = next(
                (s for s in db.get_user_servers(message.from_user.id) if s.id == server_id), None
            )
            if server is None:
                await message.reply(
                    f"Сервер с ID {server_id} не найден или не принадлежит вам.",
                    reply_markup=get_main_menu(),
                )
                db.close()
                return

            status_emoji = (
                "🟢" if server.status == "online" else "🔴" if server.status == "offline" else "⚪️"
            )
            await message.reply(
                f"Статус сервера:\n"
                f"{status_emoji} {server.name} (ID: {server.id})\n"
                f"   Адрес: {server.address}\n"
                f"   Тип проверки: {server.check_type}\n"
                f"   Статус: {server.status}",
                reply_markup=get_main_menu(),
            )
            db.close()
        except Exception as e:
            logger.error(f"Failed to check server: {e}")
            await message.reply("Не удалось проверить сервер.", reply_markup=get_main_menu())
            db.close()
    except Exception as e:
        logger.error(f"Error in process_check_server: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.", reply_markup=get_main_menu()
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
        admin_ids = (
            [id.strip() for id in config.admin_ids.split(",") if id.strip()]
            if config.admin_ids
            else []
        )
        is_admin = str(message.from_user.id) in admin_ids
        user_id_str = str(message.from_user.id)

        # Обработка числовых ID для админских команд
        if is_admin and message.text.strip().isdigit() and user_id_str in expected_id_input:
            await process_delete_user_id(message)
            return

        # Обработка общих команд меню
        menu_commands = {
            "Назад": lambda: message.reply(
                "Возвращение в главное меню.", reply_markup=get_main_menu()
            ),
            "Помощь": help_command,
            "Администратор": admin_command,
            "Список серверов": list_servers_command,
            "Добавить сервер": add_server_command,
            "Редактировать сервер": edit_server_command,
            "Удалить сервер": delete_server_command,
            "Проверить серверы": check_servers_command,
        }

        # Обработка админских команд
        admin_commands = {
            "Список пользователей": list_pending_users_command,
            "Удалить пользователя": delete_user_command,
            "Одобрить пользователя": approve_user_command,
            "Переотправить уведомление": resend_notification_command,
            "Повторно отправить уведомления": resend_notification_command,
            "Тест уведомлений": debug_notify_command,
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
            "Неизвестная команда. Воспользуйтесь кнопками меню.", reply_markup=get_main_menu()
        )

    except Exception as e:
        logger.error(f"Error in text_menu_handler: {e}")
        await message.reply(
            "Произошла ошибка. Пожалуйста, попробуйте позже.", reply_markup=get_main_menu()
        )
