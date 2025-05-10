from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_manager import DBManager
from config.config import Config
import logging

router = Router()
logger = logging.getLogger(__name__)

class AddServer(StatesGroup):
    name = State()
    address = State()
    check_type = State()

@router.message(CommandStart())
async def start_command(message: Message, db: DBManager) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username
    user = db.get_user(user_id)
    
    if not user:
        db.add_user(user_id, username)
        for admin_id in Config.ADMIN_IDS:
            await message.bot.send_message(
                admin_id,
                f"Новая заявка от пользователя @{username} (ID: {user_id})"
            )
        await message.answer("Ваша заявка отправлена на модерацию. Ожидайте одобрения.")
    elif user.status == "pending":
        await message.answer("Ваша заявка на модерации. Пожалуйста, подождите.")
    elif user.status == "rejected":
        await message.answer("Ваша заявка была отклонена. Обратитесь к администратору.")
    else:
        await message.answer(
            "Добро пожаловать! Используйте команды:\n"
            "/add_server - Добавить сервер\n"
            "/my_servers - Мои серверы\n"
            "/check_status - Проверить статус"
        )

@router.message(Command("add_server"))
async def add_server_command(message: Message, db: DBManager, state: FSMContext) -> None:
    """Обработчик команды /add_server."""
    user = db.get_user(message.from_user.id)
    if user and user.status == "approved":
        await message.answer("Введите название сервера:")
        await state.set_state(AddServer.name)
    else:
        await message.answer("У вас нет доступа. Дождитесь одобрения заявки.")

@router.message(AddServer.name)
async def process_server_name(message: Message, state: FSMContext) -> None:
    """Обработка названия сервера."""
    await state.update_data(name=message.text)
    await message.answer("Введите адрес сервера (например, example.com или 8.8.8.8):")
    await state.set_state(AddServer.address)

@router.message(AddServer.address)
async def process_server_address(message: Message, state: FSMContext) -> None:
    """Обработка адреса сервера."""
    await state.update_data(address=message.text)
    await message.answer("Выберите тип проверки (icmp, http, https):")
    await state.set_state(AddServer.check_type)

@router.message(AddServer.check_type)
async def process_check_type(message: Message, state: FSMContext, db: DBManager) -> None:
    """Обработка типа проверки."""
    check_type = message.text.lower()
    if check_type not in ["icmp", "http", "https"]:
        await message.answer("Неверный тип. Выберите: icmp, http, https")
        return
    
    data = await state.get_data()
    db.add_server(
        user_id=message.from_user.id,
        name=data["name"],
        address=data["address"],
        check_type=check_type
    )
    await message.answer(f"Сервер {data['name']} добавлен!")
    await state.clear()

@router.message(Command("my_servers"))
async def my_servers_command(message: Message, db: DBManager) -> None:
    """Обработчик команды /my_servers."""
    user = db.get_user(message.from_user.id)
    if user and user.status == "approved":
        servers = db.get_user_servers(user.id)
        if servers:
            response = "Ваши серверы:\n" + "\n".join(
                f"ID: {s.id}, Название: {s.name}, Адрес: {s.address}, Тип: {s.check_type}"
                for s in servers
            )
        else:
            response = "У вас нет серверов."
        await message.answer(response)
    else:
        await message.answer("У вас нет доступа. Дождитесь одобрения заявки.")

@router.message(Command("check_status"))
async def check_status_command(message: Message, db: DBManager) -> None:
    """Обработчик команды /check_status."""
    user = db.get_user(message.from_user.id)
    if user and user.status == "approved":
        await message.answer("Проверка статуса серверов выполняется. Уведомления придут при изменении статуса.")
    else:
        await message.answer("У вас нет доступа. Дождитесь одобрения заявки.")