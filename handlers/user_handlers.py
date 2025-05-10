from aiogram import Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database.db_manager import DBManager
import logging
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Добавить сервер"))
    keyboard.add(KeyboardButton("Мои серверы"))
    keyboard.add(KeyboardButton("Проверить серверы"))
    keyboard.add(KeyboardButton("Редактировать сервер"))
    keyboard.add(KeyboardButton("Удалить сервер"))
    return keyboard

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def start_command(message: Message):
        logger.info(f"Received /start from user {message.from_user.id}")
        try:
            db = DBManager()
            user = db.get_user(message.from_user.id)
            if user is None:
                db.add_user(message.from_user.id, message.from_user.username or "unknown")
                await message.reply("Заявка на регистрацию отправлена. Ожидайте одобрения администратора.")
            elif user.status == 'pending':
                await message.reply("Ваша заявка на рассмотрении.")
            elif user.status == 'approved':
                await message.reply(
                    "Добро пожаловать в бот мониторинга серверов!",
                    reply_markup=get_main_menu()
                )
            db.close()
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.message_handler(commands=['help'])
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
            "/check_servers - Проверить статус серверов"
        )

    @dp.message_handler(commands=['add_server'], regexp_commands=['add_server'])
    async def add_server_command(message: Message):
        logger.info(f"Received /add_server from user {message.from_user.id}")
        try:
            db = DBManager()
            user = db.get_user(message.from_user.id)
            if user is None or user.status != 'approved':
                await message.reply("Вы не зарегистрированы или не одобрены.", reply_markup=get_main_menu())
                db.close()
                return
            await message.reply(
                "Введите данные сервера в формате: название, адрес, тип (icmp, http, https)\n"
                "Пример: Мой сервер, example.com:80, http"
            )
            db.close()
            dp.register_message_handler(process_add_server, content_types=['text'])
        except Exception as e:
            logger.error(f"Error in add_server_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    async def process_add_server(message: Message):
        logger.info(f"Processing server data from user {message.from_user.id}")
        try:
            data = message.text.split(',')
            if len(data) != 3:
                raise ValueError("Неверный формат. Пример: Мой сервер, example.com:80, http")
            name, address, check_type = [d.strip() for d in data]
            if check_type not in ['icmp', 'http', 'https']:
                raise ValueError("Тип проверки должен быть icmp, http или https")
            if not re.match(r'^[\w\s-]+$', name):
                raise ValueError("Название содержит недопустимые символы")
            if not re.match(
                r'^(?:\d{1,3}\.){3}\d{1,3}$|^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::\d{1,5})?$',
                address
            ):
                raise ValueError("Неверный адрес сервера (IP, домен или домен:порт)")

            db = DBManager()
            db.add_server(message.from_user.id, name, address, check_type)
            await message.reply(f"Сервер '{name}' добавлен.", reply_markup=get_main_menu())
            db.close()
        except Exception as e:
            logger.error(f"Error in process_add_server: {e}")
            await message.reply(f"Ошибка: {str(e)}")
        finally:
            dp.message_handlers.unregister(process_add_server)

    @dp.message_handler(commands=['list_servers'], regexp_commands=['list_servers'])
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
                    response += f"ID: {server.id}, {server.name} ({server.address}, {server.check_type}): {server.status}\n"
                await message.reply(response, reply_markup=get_main_menu())
            db.close()
        except Exception as e:
            logger.error(f"Error in list_servers_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.message_handler(commands=['edit_server'], regexp_commands=['edit_server'])
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
            await message.reply(
                "Введите ID сервера и новые данные в формате: ID, название, адрес, тип\n"
                "Пример: 1, Новый сервер, 1.1.1.1, icmp"
            )
            db.close()
            dp.register_message_handler(process_edit_server, content_types=['text'])
        except Exception as e:
            logger.error(f"Error in edit_server_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    async def process_edit_server(message: Message):
        logger.info(f"Processing edit server data from user {message.from_user.id}")
        try:
            data = message.text.split(',')
            if len(data) != 4:
                raise ValueError("Неверный формат. Пример: 1, Новый сервер, 1.1.1.1, icmp")
            server_id, name, address, check_type = [d.strip() for d in data]
            server_id = int(server_id)
            if check_type not in ['icmp', 'http', 'https']:
                raise ValueError("Тип проверки должен быть icmp, http или https")
            if not re.match(r'^[\w\s-]+$', name):
                raise ValueError("Название содержит недопустимые символы")
            if not re.match(
                r'^(?:\d{1,3}\.){3}\d{1,3}$|^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::\d{1,5})?$',
                address
            ):
                raise ValueError("Неверный адрес сервера (IP, домен или домен:порт)")

            db = DBManager()
            servers = db.get_user_servers(message.from_user.id)
            if not any(s.id == server_id for s in servers):
                raise ValueError("Сервер с указанным ID не найден")
            db.update_server(server_id, name, address, check_type)
            await message.reply(f"Сервер ID {server_id} обновлён.", reply_markup=get_main_menu())
            db.close()
        except Exception as e:
            logger.error(f"Error in process_edit_server: {e}")
            await message.reply(f"Ошибка: {str(e)}")
        finally:
            dp.message_handlers.unregister(process_edit_server)

    @dp.message_handler(commands=['delete_server'], regexp_commands=['delete_server'])
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
            await message.reply("Введите ID сервера для удаления.")
            db.close()
            dp.register_message_handler(process_delete_server, content_types=['text'])
        except Exception as e:
            logger.error(f"Error in delete_server_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    async def process_delete_server(message: Message):
        logger.info(f"Processing delete server from user {message.from_user.id}")
        try:
            server_id = int(message.text.strip())
            db = DBManager()
            servers = db.get_user_servers(message.from_user.id)
            if not any(s.id == server_id for s in servers):
                raise ValueError("Сервер с указанным ID не найден")
            db.delete_server(server_id)
            await message.reply(f"Сервер ID {server_id} удалён.", reply_markup=get_main_menu())
            db.close()
        except Exception as e:
            logger.error(f"Error in process_delete_server: {e}")
            await message.reply(f"Ошибка: {str(e)}")
        finally:
            dp.message_handlers.unregister(process_delete_server)

    @dp.message_handler(commands=['check_servers'], regexp_commands=['check_servers'])
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
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            for server in servers:
                keyboard.add(KeyboardButton(f"Проверить {server.name}"))
            keyboard.add(KeyboardButton("Назад"))
            await message.reply("Выберите сервер для проверки:", reply_markup=keyboard)
            db.close()
            dp.register_message_handler(process_check_server, content_types=['text'])
        except Exception as e:
            logger.error(f"Error in check_servers_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    async def process_check_server(message: Message):
        logger.info(f"Processing server check from user {message.from_user.id}")
        try:
            if message.text == "Назад":
                await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
                dp.message_handlers.unregister(process_check_server)
                return
            db = DBManager()
            servers = db.get_user_servers(message.from_user.id)
            server_name = message.text.replace("Проверить ", "")
            server = next((s for s in servers if s.name == server_name), None)
            if server:
                await message.reply(f"Статус сервера {server.name} ({server.address}): {server.status}")
            else:
                await message.reply("Сервер не найден.")
            db.close()
        except Exception as e:
            logger.error(f"Error in process_check_server: {e}")
            await message.reply(f"Ошибка: {str(e)}")
        finally:
            dp.message_handlers.unregister(process_check_server)

    @dp.message_handler(content_types=['text'])
    async def text_menu_handler(message: Message):
        logger.info(f"Received text menu command from user {message.from_user.id}: {message.text}")
        try:
            if message.text == "Добавить сервер":
                await add_server_command(message)
            elif message.text == "Мои серверы":
                await list_servers_command(message)
            elif message.text == "Проверить серверы":
                await check_servers_command(message)
            elif message.text == "Редактировать сервер":
                await edit_server_command(message)
            elif message.text == "Удалить сервер":
                await delete_server_command(message)
        except Exception as e:
            logger.error(f"Error in text_menu_handler: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")