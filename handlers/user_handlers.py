from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from database.db_manager import DatabaseManager
from database.models import User, Server
from config.config import Config
from datetime import datetime
from aiogram.dispatcher.filters.state import State, StatesGroup

class AddServer(StatesGroup):
    name = State()
    address = State()
    check_type = State()

class EditServer(StatesGroup):
    server_id = State()
    name = State()
    address = State()
    check_type = State()

def get_server_management_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Добавить сервер", callback_data="add_server"))
    keyboard.add(InlineKeyboardButton(text="Мои сервера", callback_data="list_servers"))
    keyboard.add(InlineKeyboardButton(text="Проверить статус", callback_data="check_status"))
    return keyboard

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=["start"])
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
            # Уведомление админов
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
            await message.answer("Добро пожаловать! Управление серверами:", reply_markup=get_server_management_menu())

    @dp.callback_query_handler(lambda c: c.data == "add_server")
    async def add_server_start(callback: CallbackQuery, db: DatabaseManager, state: FSMContext):
        user = await db.get_user(callback.from_user.id)
        if not user or user.status != "approved":
            await callback.message.answer("Доступ запрещен или заявка не одобрена.")
            await callback.answer()
            return
        await callback.message.answer("Введите название сервера:")
        await state.set_state(AddServer.name)
        await callback.answer()

    @dp.message_handler(state=AddServer.name)
    async def process_server_name(message: Message, state: FSMContext):
        await state.update_data(name=message.text)
        await message.answer("Введите адрес сервера (например, example.com или 192.168.1.1):")
        await state.set_state(AddServer.address)

    @dp.message_handler(state=AddServer.address)
    async def process_server_address(message: Message, state: FSMContext):
        await state.update_data(address=message.text)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="ICMP", callback_data="type_icmp"))
        keyboard.add(InlineKeyboardButton(text="HTTP", callback_data="type_http"))
        keyboard.add(InlineKeyboardButton(text="HTTPS", callback_data="type_https"))
        await message.answer("Выберите тип проверки:", reply_markup=keyboard)
        await state.set_state(AddServer.check_type)

    @dp.callback_query_handler(lambda c: c.data.startswith("type_"), state=AddServer.check_type)
    async def process_server_type(callback: CallbackQuery, state: FSMContext, db: DatabaseManager):
        check_type = callback.data.split("_")[1]
        user_data = await state.get_data()
        server = Server(
            id=0,
            user_id=callback.from_user.id,
            name=user_data["name"],
            address=user_data["address"],
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
        await state.finish()
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "list_servers")
    async def list_servers(callback: CallbackQuery, db: DatabaseManager):
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
        for server in servers:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{server.id}"))
            keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"delete_{server.id}"))
            await callback.message.answer(
                f"Сервер ID: {server.id}\n"
                f"Название: {server.name}\n"
                f"Адрес: {server.address}\n"
                f"Тип: {server.check_type}",
                reply_markup=keyboard
            )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data.startswith("edit_"))
    async def edit_server_start(callback: CallbackQuery, db: DatabaseManager, state: FSMContext):
        user = await db.get_user(callback.from_user.id)
        if not user or user.status != "approved":
            await callback.message.answer("Доступ запрещен или заявка не одобрена.")
            await callback.answer()
            return
        server_id = int(callback.data.split("_")[1])
        server = await db.get_server(server_id, callback.from_user.id)
        if not server:
            await callback.message.answer("Сервер не найден или не принадлежит вам.")
            await callback.answer()
            return
        await state.update_data(server_id=server_id)
        await callback.message.answer(f"Текущее название: {server.name}\nВведите новое название:")
        await state.set_state(EditServer.name)
        await callback.answer()

    @dp.message_handler(state=EditServer.name)
    async def process_edit_server_name(message: Message, state: FSMContext):
        await state.update_data(name=message.text)
        await message.answer("Введите новый адрес сервера:")
        await state.set_state(EditServer.address)

    @dp.message_handler(state=EditServer.address)
    async def process_edit_server_address(message: Message, state: FSMContext):
        await state.update_data(address=message.text)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="ICMP", callback_data="edit_type_icmp"))
        keyboard.add(InlineKeyboardButton(text="HTTP", callback_data="edit_type_http"))
        keyboard.add(InlineKeyboardButton(text="HTTPS", callback_data="edit_type_https"))
        await message.answer("Выберите новый тип проверки:", reply_markup=keyboard)
        await state.set_state(EditServer.check_type)

    @dp.callback_query_handler(lambda c: c.data.startswith("edit_type_"), state=EditServer.check_type)
    async def process_edit_server_type(callback: CallbackQuery, state: FSMContext, db: DatabaseManager):
        check_type = callback.data.split("_")[2]
        user_data = await state.get_data()
        server_id = user_data["server_id"]
        success = await db.update_server(
            server_id=server_id,
            user_id=callback.from_user.id,
            name=user_data["name"],
            address=user_data["address"],
            check_type=check_type
        )
        if success:
            await callback.message.answer(
                f"Сервер обновлен:\n"
                f"Название: {user_data['name']}\n"
                f"Адрес: {user_data['address']}\n"
                f"Тип: {check_type}"
            )
        else:
            await callback.message.answer("Не удалось обновить сервер.")
        await state.finish()
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data.startswith("delete_"))
    async def delete_server(callback: CallbackQuery, db: DatabaseManager):
        user = await db.get_user(callback.from_user.id)
        if not user or user.status != "approved":
            await callback.message.answer("Доступ запрещен или заявка не одобрена.")
            await callback.answer()
            return
        server_id = int(callback.data.split("_")[1])
        success = await db.delete_server(server_id, callback.from_user.id)
        if success:
            await callback.message.answer(f"Сервер с ID {server_id} удален.")
        else:
            await callback.message.answer("Не удалось удалить сервер.")
        await callback.answer()