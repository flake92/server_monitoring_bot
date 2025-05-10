from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db_manager import DatabaseManager
from database.models import User, Server
from config.config import Config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

router = Router()

class AddServerForm(StatesGroup):
    name = State()
    address = State()
    check_type = State()

class EditServerForm(StatesGroup):
    server_id = State()
    name = State()
    address = State()
    check_type = State()

def get_server_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить сервер", callback_data="add_server")],
        [InlineKeyboardButton(text="Мои сервера", callback_data="list_servers")],
    ])
    return keyboard

@router.message(Command("start"))
async def start_command(message: Message, db: DatabaseManager):
    user = await db.get_user(message.from_user.id)
    if not user:
        new_user = User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await db.add_user(new_user)
        await message.answer(
            "Ваша заявка на использование бота отправлена на модерацию. "
            "Ожидайте подтверждения от администратора."
        )
        for admin_id in Config.ADMIN_IDS:
            await message.bot.send_message(
                admin_id,
                f"Новая заявка на модерацию:\n"
                f"ID: {new_user.user_id}\n"
                f"Username: @{new_user.username}\n"
                f"Имя: {new_user.first_name} {new_user.last_name}"
            )
    elif user.status == "pending":
        await message.answer("Ваша заявка на рассмотрении.")
    elif user.status == "rejected":
        await message.answer("Ваша заявка была отклонена.")
    else:
        await message.answer("Добро пожаловать! Управление серверами:", reply_markup=get_server_menu())

@router.callback_query(F.data == "add_server")
async def add_server_start(callback: CallbackQuery, db: DatabaseManager, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    if not user or user.status != "approved":
        await callback.message.answer("Доступ запрещен или заявка не одобрена.")
        return
    await callback.message.answer("Введите название сервера:")
    await state.set_state(AddServerForm.name)
    await callback.answer()

@router.message(AddServerForm.name)
async def process_server_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите адрес сервера (например, example.com или 192.168.1.1):")
    await state.set_state(AddServerForm.address)

@router.message(AddServerForm.address)
async def process_server_address(message: message, state: FSMContext):
    await state.update_data(address=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ICMP", callback_data="check_icmp")],
        [InlineKeyboardButton(text="HTTP", callback_data="check_http")],
        [InlineKeyboardButton(text="HTTPS", callback_data="check_https")]
    ])
    await message.answer("Выберите тип проверки:", reply_markup=keyboard)
    await state.set_state(AddServerForm.check_type)

@router.callback_query(F.data.startswith("check_"))
async def process_check_type(callback: CallbackQuery, state: FSMContext, db: DatabaseManager):
    check_type = callback.data.split("_")[1]
    data = await state.get_data()
    server = Server(
        id=0,
        user_id=callback.from_user.id,
        name=data["name"],
        address=data["address"],
        check_type=check_type,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    await db.add_server(server)
    await callback.message.answer(
        f"Сервер добавлен:\n"
        f"Название: {server.name}\n"
        f"Адрес: {server.address}\n"
        f"Тип: {server.check_type}"
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "list_servers")
async def list_servers(callback: CallbackQuery, db: DatabaseManager):
    user = await db.get_user(callback.from_user.id)
    if not user or user.status != "approved":
        await callback.message.answer("Доступ запрещен или заявка не одобрена.")
        return
    servers = await db.get_user_servers(callback.from_user.id)
    if not servers:
        await callback.message.answer("У вас нет добавленных серверов.")
        return
    for server in servers:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Редактировать", callback_data=f"edit_server_{server.id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete_server_{server.id}")]
        ])
        await callback.message.answer(
            f"Сервер: {server.name}\n"
            f"Адрес: {server.address}\n"
            f"Тип: {server.check_type}",
            reply_markup=keyboard
        )
    await callback.answer()

@router.callback_query(F.data.startswith("edit_server_"))
async def edit_server_start(callback: CallbackQuery, db: DatabaseManager, state: FSMContext):
    server_id = int(callback.data.split("_")[2])
    server = await db.get_server(server_id, callback.from_user.id)
    if not server:
        await callback.message.answer("Сервер не найден.")
        return
    await state.update_data(server_id=server_id)
    await callback.message.answer(f"Текущее название: {server.name}\nВведите новое название:")
    await state.set_state(EditServerForm.name)
    await callback.answer()

@router.message(EditServerForm.name)
async def process_edit_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите новый адрес сервера:")
    await state.set_state(EditServerForm.address)

@router.message(EditServerForm.address)
async def process_edit_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ICMP", callback_data="edit_check_icmp")],
        [InlineKeyboardButton(text="HTTP", callback_data="edit_check_http")],
        [InlineKeyboardButton(text="HTTPS", callback_data="edit_check_https")]
    ])
    await message.answer("Выберите новый тип проверки:", reply_markup=keyboard)
    await state.set_state(EditServerForm.check_type)

@router.callback_query(F.data.startswith("edit_check_"))
async def process_edit_check_type(callback: CallbackQuery, state: FSMContext, db: DatabaseManager):
    check_type = callback.data.split("_")[2]
    data = await state.get_data()
    await db.update_server(
        server_id=data["server_id"],
        user_id=callback.from_user.id,
        name=data["name"],
        address=data["address"],
        check_type=check_type
    )
    await callback.message.answer(
        f"Сервер обновлен:\n"
        f"Название: {data['name']}\n"
        f"Адрес: {data['address']}\n"
        f"Тип: {check_type}"
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("delete_server_"))
async def delete_server(callback: CallbackQuery, db: DatabaseManager):
    server_id = int(callback.data.split("_")[2])
    server = await db.get_server(server_id, callback.from_user.id)
    if not server:
        await callback.message.answer("Сервер не найден.")
        return
    await db.delete_server(server_id, callback.from_user.id)
    await callback.message.answer(f"Сервер {server.name} удален.")
    await callback.answer()