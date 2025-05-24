import re
from enum import Enum

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from pydantic import HttpUrl, ValidationError

from config.config import Config
from database.db_manager import DBManager
from services.monitoring import MonitoringService
from utils.logger import setup_logger

router = Router()
logger = setup_logger(__name__)

class UserState(Enum):
    ADD_SERVER = "add_server"
    DELETE_USER = "delete_user"
    EDIT_SERVER = "edit_server"
    DELETE_SERVER = "delete_server"
    CHECK_SERVER = "check_server"

class AddServerFSM(StatesGroup):
    address = State()
    name = State()

class EditServerFSM(StatesGroup):
    select_server = State()
    address = State()

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

def is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids

async def validate_server_address(address: str) -> tuple[str, int, str]:
    try:
        url = HttpUrl(address)
        return url.host, url.port or 80, url.scheme
    except ValidationError:
        if ":" in address:
            host, port = address.rsplit(":", 1)
            try:
                port = int(port)
                if not 1 <= port <= 65535:
                    raise ValueError("Port must be between 1 and 65535")
                return host, port, "http"
            except ValueError:
                raise ValueError("Invalid port")
        raise ValueError("Invalid server address")

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    logger.info(f"Received /start from user {message.from_user.id}")
    try:
        config = Config.from_env()
        async with DBManager(config) as db:
            user = await db.get_user(message.from_user.id)
            if not user:
                status = "approved" if is_admin(message.from_user.id, config) else "pending"
                username = message.from_user.username or "unknown"
                await db.add_user(message.from_user.id, username, status)
                if is_admin(message.from_user.id, config):
                    await message.reply(f"{EMOJI['WAVE']} Добро пожаловать, администратор!", reply_markup=get_main_menu())
                else:
                    for admin_id in config.admin_ids:
                        await message.bot.send_message(admin_id, f"{EMOJI['LIST']} Новая заявка: @{username} (ID: {message.from_user.id})")
                    await message.reply(f"{EMOJI['SUCCESS']} Заявка отправлена на одобрение")
                return
            if user["status"] == "pending" and is_admin(message.from_user.id, config):
                await db.update_user_status(message.from_user.id, "approved")
                await message.reply(f"{EMOJI['UNLOCK']} Ваш статус обновлён!", reply_markup=get_main_menu())
            elif user["status"] == "pending":
                await message.reply(f"{EMOJI['PENDING']} Заявка на рассмотрении")
            elif user["status"] == "approved":
                await message.reply(f"{EMOJI['WAVE']} Добро пожаловать!", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply("Ошибка. Попробуйте позже.")

@router.message(Command("help"))
async def help_command(message: Message):
    logger.info(f"Received /help from user {message.from_user.id}")
    config = Config.from_env()
    help_text = (
        "📋 Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/add_server - Добавить новый сервер\n"
        "/list_servers - Показать список серверов\n"
        "/edit_server - Редактировать сервер\n"
        "/delete_server - Удалить сервер\n"
        "/check_servers - Проверить статус серверов\n"
        "/monitor - Мониторинг серверов\n"
    )
    if is_admin(message.from_user.id, config):
        help_text += (
            "\nКоманды администратора:\n"
            "/admin - Панель администратора\n"
            "/list_pending_users - Список пользователей с ожидающими заявками\n"
            "/approve_user - Одобрить пользователя\n"
            "/delete_user - Удалить пользователя\n"
            "/debug_notify - Отправить тестовое уведомление\n"
        )
    await message.reply(help_text)

@router.message(Command("admin"))
async def admin_command(message: Message):
    logger.info(f"Received /admin from user {message.from_user.id}")
    config = Config.from_env()
    if not is_admin(message.from_user.id, config):
        await message.reply(f"{EMOJI['DENIED']} Доступ запрещён")
        return
    await message.reply(f"{EMOJI['SETTINGS']} Панель администратора:", reply_markup=get_admin_menu())

@router.message(Command("add_server"))
async def add_server_command(message: Message, state: FSMContext):
    logger.info(f"Received /add_server from user {message.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        user = await db.get_user(message.from_user.id)
        if not user or user["status"] != "approved":
            await message.reply("У вас нет прав для добавления серверов.")
            return
        await state.set_state(AddServerFSM.address)
        await message.reply(
            "Введите адрес сервера (например, http://example.com:80):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
            )
        )

@router.message(AddServerFSM.address, F.text)
async def process_server_address(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return
    try:
        host, port, scheme = await validate_server_address(message.text)
        await state.update_data(host=host, port=port, scheme=scheme)
        await state.set_state(AddServerFSM.name)
        await message.reply("Введите название сервера:")
    except ValueError as e:
        await message.reply(f"Ошибка: {str(e)}. Попробуйте снова.")

@router.message(AddServerFSM.name, F.text)
async def process_server_name(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return
    config = Config.from_env()
    async with DBManager(config) as db:
        try:
            data = await state.get_data()
            server_id = await db.add_server(
                user_id=message.from_user.id,
                name=message.text,
                address=f"{data['host']}:{data['port']}",
                check_type=data['scheme']
            )
            await message.reply(f"Сервер {message.text} успешно добавлен (ID: {server_id})", reply_markup=get_main_menu())
            await state.clear()
        except Exception as e:
            logger.error(f"Error adding server: {e}")
            await message.reply("Не удалось добавить сервер.", reply_markup=get_main_menu())

@router.message(Command("list_servers"))
async def list_servers_command(message: Message):
    logger.info(f"Received /list_servers from user {message.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        user = await db.get_user(message.from_user.id)
        if not user or user["status"] != "approved":
            await message.reply("У вас нет прав для просмотра серверов.")
            return
        servers = await db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            return
        response = "Ваши серверы:\n"
        for server in servers:
            status_emoji = EMOJI["ONLINE"] if server["status"] == "online" else EMOJI["OFFLINE"] if server["status"] == "offline" else "⚪️"
            response += f"{status_emoji} {server['name']} (ID: {server['id']})\n"
            response += f"   Адрес: {server['address']}\n"
            response += f"   Тип проверки: {server['check_type']}\n"
            response += f"   Статус: {server['status']}\n\n"
        await message.reply(response, reply_markup=get_main_menu())

@router.message(Command("edit_server"))
async def edit_server_command(message: Message, state: FSMContext):
    logger.info(f"Received /edit_server from user {message.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        user = await db.get_user(message.from_user.id)
        if not user or user["status"] != "approved":
            await message.reply("У вас нет прав для редактирования серверов.")
            return
        servers = await db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            return
        response = "Выберите сервер для редактирования:\n\n"
        for server in servers:
            status_emoji = EMOJI["ONLINE"] if server["status"] == "online" else EMOJI["OFFLINE"] if server["status"] == "offline" else "⚪️"
            response += f"{status_emoji} {server['name']} (ID: {server['id']})\n"
            response += f"   Адрес: {server['address']}\n"
            response += f"   Тип проверки: {server['check_type']}\n\n"
        await state.set_state(EditServerFSM.select_server)
        await message.reply(response + "Введите ID сервера:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
        ))

@router.message(EditServerFSM.select_server, F.text)
async def process_edit_server_id(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return
    config = Config.from_env()
    async with DBManager(config) as db:
        try:
            server_id = int(message.text)
            servers = await db.get_user_servers(message.from_user.id)
            server = next((s for s in servers if s["id"] == server_id), None)
            if not server:
                await message.reply("Сервер не найден.", reply_markup=get_main_menu())
                await state.clear()
                return
            await state.update_data(server_id=server_id)
            await state.set_state(EditServerFSM.address)
            await message.reply(f"Введите новый адрес для сервера {server['name']} (например, http://example.com:80):")
        except ValueError:
            await message.reply("ID должен быть числом.")

@router.message(EditServerFSM.address, F.text)
async def process_edit_server_address(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return
    config = Config.from_env()
    async with DBManager(config) as db:
        try:
            data = await state.get_data()
            server_id = data["server_id"]
            host, port, scheme = await validate_server_address(message.text)
            await db.update_server(server_id, f"Server {host}:{port}", f"{host}:{port}", scheme)
            await message.reply(f"Сервер с ID {server_id} обновлён.", reply_markup=get_main_menu())
            await state.clear()
        except ValueError as e:
            await message.reply(f"Ошибка: {str(e)}. Попробуйте снова.")

@router.message(Command("delete_server"))
async def delete_server_command(message: Message, state: FSMContext):
    logger.info(f"Received /delete_server from user {message.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        user = await db.get_user(message.from_user.id)
        if not user or user["status"] != "approved":
            await message.reply("У вас нет прав для удаления серверов.")
            return
        servers = await db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            return
        response = "Выберите сервер для удаления:\n\n"
        for server in servers:
            status_emoji = EMOJI["ONLINE"] if server["status"] == "online" else EMOJI["OFFLINE"] if server["status"] == "offline" else "⚪️"
            response += f"{status_emoji} {server['name']} (ID: {server['id']})\n"
            response += f"   Адрес: {server['address']}\n"
            response += f"   Тип проверки: {server['check_type']}\n\n"
        await state.set_state(UserState.DELETE_SERVER.value)
        await message.reply(response + "Введите ID сервера:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
        ))

@router.message(F.text, UserState.DELETE_SERVER.value)
async def process_delete_server(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return
    config = Config.from_env()
    async with DBManager(config) as db:
        try:
            server_id = int(message.text)
            servers = await db.get_user_servers(message.from_user.id)
            server = next((s for s in servers if s["id"] == server_id), None)
            if not server:
                await message.reply("Сервер не найден.", reply_markup=get_main_menu())
                await state.clear()
                return
            await db.delete_server(server_id)
            await message.reply(f"Сервер {server['name']} удалён.", reply_markup=get_main_menu())
            await state.clear()
        except ValueError:
            await message.reply("ID должен быть числом.")

@router.message(Command("check_servers"))
async def check_servers_command(message: Message, state: FSMContext):
    logger.info(f"Received /check_servers from user {message.from_user.id}")
    config = Config.from_env()
    async with DBManager(config) as db:
        user = await db.get_user(message.from_user.id)
        if not user or user["status"] != "approved":
            await message.reply("У вас нет прав для проверки серверов.")
            return
        servers = await db.get_user_servers(message.from_user.id)
        if not servers:
            await message.reply("У вас нет серверов.", reply_markup=get_main_menu())
            return
        response = "Выберите сервер для проверки:\n\n"
        for server in servers:
            status_emoji = EMOJI["ONLINE"] if server["status"] == "online" else EMOJI["OFFLINE"] if server["status"] == "offline" else "⚪️"
            response += f"{status_emoji} {server['name']} (ID: {server['id']})\n"
            response += f"   Адрес: {server['address']}\n"
            response += f"   Тип проверки: {server['check_type']}\n\n"
        await state.set_state(UserState.CHECK_SERVER.value)
        await message.reply(response + "Введите ID сервера:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
        ))

@router.message(F.text, UserState.CHECK_SERVER.value)
async def process_check_server(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
        return
    config = Config.from_env()
    async with DBManager(config) as db:
        async with MonitoringService(config) as monitoring:
            try:
                server_id = int(message.text)
                servers = await db.get_user_servers(message.from_user.id)
                server = next((s for s in servers if s["id"] == server_id), None)
                if not server:
                    await message.reply("Сервер не найден.", reply_markup=get_main_menu())
                    await state.clear()
                    return
                status = await monitoring.check_server(server)
                await db.update_server_status(
                    server_id,
                    "online" if status.is_online else "offline",
                    status.last_checked,
                    status.response_time,
                    status.error_message
                )
                status_emoji = EMOJI["ONLINE"] if status.is_online else EMOJI["OFFLINE"]
                await message.reply(
                    f"Статус сервера:\n"
                    f"{status_emoji} {server['name']} (ID: {server['id']})\n"
                    f"   Адрес: {server['address']}\n"
                    f"   Тип проверки: {server['check_type']}\n"
                    f"   Статус: {'online' if status.is_online else 'offline'}",
                    reply_markup=get_main_menu()
                )
                await state.clear()
            except ValueError:
                await message.reply("ID должен быть числом.")

@router.message(Command("delete_user"))
async def delete_user_command(message: Message, state: FSMContext):
    logger.info(f"Received /delete_user from user {message.from_user.id}")
    config = Config.from_env()
    if not is_admin(message.from_user.id, config):
        await message.reply(f"{EMOJI['DENIED']} Доступ запрещён")
        return
    await state.set_state(UserState.DELETE_USER.value)
    await message.reply("Введите ID пользователя для удаления:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
    ))

@router.message(F.text, UserState.DELETE_USER.value)
async def process_delete_user(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в главное меню.", reply_markup=get_admin_menu())
        return
    config = Config.from_env()
    async with DBManager(config) as db:
        try:
            user_id = int(message.text)
            user = await db.get_user(user_id)
            if not user:
                await message.reply("Пользователь не найден.", reply_markup=get_admin_menu())
                await state.clear()
                return
            await db.delete_user(user_id)
            await message.reply(f"Пользователь {user['username']} удалён.", reply_markup=get_admin_menu())
            try:
                await message.bot.send_message(user_id, "Ваш аккаунт удалён.")
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
            await state.clear()
        except ValueError:
            await message.reply("ID должен быть числом.")

@router.message(Command("approve_user"))
async def approve_user_command(message: Message, state: FSMContext):
    logger.info(f"Received /approve_user from user {message.from_user.id}")
    config = Config.from_env()
    if not is_admin(message.from_user.id, config):
        await message.reply(f"{EMOJI['DENIED']} Доступ запрещён")
        return
    await state.set_state("approve_user")
    await message.reply("Введите ID пользователя для одобрения:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
    ))

@router.message(F.text, state="approve_user")
async def process_approve_user(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.reply("Возвращение в админ-меню.", reply_markup=get_admin_menu())
        return
    config = Config.from_env()
    async with DBManager(config) as db:
        try:
            user_id = int(message.text)
            user = await db.get_user(user_id)
            if not user:
                await message.reply("Пользователь не найден.", reply_markup=get_admin_menu())
                await state.clear()
                return
            await db.update_user_status(user_id, "approved")
            await message.reply(f"Пользователь {user['username']} одобрен.", reply_markup=get_admin_menu())
            try:
                await message.bot.send_message(user_id, "Ваша заявка одобрена!")
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
            await state.clear()
        except ValueError:
            await message.reply("ID должен быть числом.")

@router.message(Command("list_pending_users"))
async def list_pending_users_command(message: Message):
    logger.info(f"Received /list_pending_users from user {message.from_user.id}")
    config = Config.from_env()
    if not is_admin(message.from_user.id, config):
        await message.reply(f"{EMOJI['DENIED']} Доступ запрещён")
        return
    async with DBManager(config) as db:
        pending_users = await db.get_pending_users()
        if not pending_users:
            await message.reply(f"{EMOJI['EMPTY']} Нет ожидающих заявок", reply_markup=get_admin_menu())
            return
        response = "Ожидающие заявки:\n\n"
        for user in pending_users:
            response += f"ID: {user['id']}\nИмя: {user['username']}\nДата: {user['created_at']}\n---\n"
        await message.reply(response, reply_markup=get_admin_menu())

@router.message(Command("debug_notify"))
async def debug_notify_command(message: Message):
    logger.info(f"Received /debug_notify from user {message.from_user.id}")
    config = Config.from_env()
    if not is_admin(message.from_user.id, config):
        await message.reply(f"{EMOJI['DENIED']} Доступ запрещён")
        return
    await message.reply(f"{EMOJI['SUCCESS']} Тестовое уведомление отправлено", reply_markup=get_admin_menu())
    # Реализация отправки тестового уведомления зависит от notification.py