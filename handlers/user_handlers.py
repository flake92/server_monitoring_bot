from aiogram import Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from database.db_manager import DBManager
from config.config import Config
import logging
import re
from datetime import datetime, timedelta
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

def get_admin_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Список ожидающих пользователей"))
    keyboard.add(KeyboardButton("Одобрить пользователя"))
    keyboard.add(KeyboardButton("Удалить пользователя"))
    keyboard.add(KeyboardButton("Повторно отправить уведомления"))
    keyboard.add(KeyboardButton("Тест уведомлений"))
    keyboard.add(KeyboardButton("Назад"))
    return keyboard

class AdminState(StatesGroup):
    waiting_for_approve_id = State()
    waiting_for_delete_id = State()

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def start_command(message: Message):
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
                    # Уведомление администраторов о новой заявке
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
                                # Попытка уведомить других админов об ошибке
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
            "/check_servers - Проверить статус серверов\n"
            "/admin - Админ-панель (для администраторов)\n"
            "/debug_notify - Проверить уведомления (для администраторов)\n"
            "/list_pending_users - Показать пользователей с ожидающими заявками (для администраторов)\n"
            "/delete_user - Удалить пользователя (для администраторов)\n"
            "/approve_user - Одобрить заявку пользователя (для администраторов)\n"
            "/resend_notification - Повторно отправить уведомления о заявках (для администраторов)"
        )

    @dp.message_handler(commands=['admin'])
    async def admin_command(message: Message):
        logger.info(f"Received /admin from user {message.from_user.id}")
        try:
            config = Config()
            admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
            logger.info(f"Parsed admin_ids for admin: {admin_ids}")
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

    @dp.message_handler(commands=['debug_notify'])
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
            if admin_ids:
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
            else:
                logger.error("No admin IDs configured for debug_notify")
                await message.reply("Ошибка: список администраторов пуст.")
        except Exception as e:
            logger.error(f"Error in debug_notify_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.")

    @dp.message_handler(commands=['list_pending_users'])
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

    @dp.message_handler(commands=['delete_user'])
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

    @dp.message_handler(commands=['approve_user'])
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

    @dp.message_handler(commands=['resend_notification'])
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
                            f"Повторное уведомление о заявке:\n"
                            f"Пользователь: @{user.username or 'unknown'} (ID: {user.id})"
                        )
                        logger.info(f"Sent notification about pending user {user.id} to admin {admin_id}")
                    except Exception as e:
                        logger.error(f"Failed to send notification about user {user.id} to admin {admin_id}: {e}")
                        await message.reply(
                            f"Ошибка при отправке уведомления админу {admin_id} о пользователе {user.id}: {str(e)}",
                            reply_markup=get_admin_menu()
                        )
            db.update_notification_time(current_time)
            await message.reply(f"Отправлены уведомления о {len(pending_users)} ожидающих заявках.", reply_markup=get_admin_menu())
            db.close()
        except Exception as e:
            logger.error(f"Error in resend_notification_command: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())

    @dp.message_handler(commands=['add_server'])
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

    @dp.message_handler(commands=['list_servers'])
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

    @dp.message_handler(commands=['edit_server'])
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

    @dp.message_handler(commands=['delete_server'])
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

    @dp.message_handler(commands=['check_servers'])
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

    @dp.message_handler(state=AdminState.waiting_for_approve_id)
    async def process_approve_user_id(message: Message, state: FSMContext):
        logger.info(f"Processing approve user ID from user {message.from_user.id}")
        try:
            config = Config()
            admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
            if str(message.from_user.id) not in admin_ids:
                logger.warning(f"Access denied for user {message.from_user.id}")
                await message.reply("Доступ запрещён.")
                await state.finish()
                return
            try:
                user_id = int(message.text.strip())
            except ValueError:
                await message.reply("ID пользователя должен быть числом.", reply_markup=get_admin_menu())
                await state.finish()
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
            logger.error(f"Error in process_approve_user_id: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())
        finally:
            await state.finish()

    @dp.message_handler(state=AdminState.waiting_for_delete_id)
    async def process_delete_user_id(message: Message, state: FSMContext):
        logger.info(f"Processing delete user ID from user {message.from_user.id}")
        try:
            config = Config()
            admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
            if str(message.from_user.id) not in admin_ids:
                logger.warning(f"Access denied for user {message.from_user.id}")
                await message.reply("Доступ запрещён.")
                await state.finish()
                return
            try:
                user_id = int(message.text.strip())
            except ValueError:
                await message.reply("ID пользователя должен быть числом.", reply_markup=get_admin_menu())
                await state.finish()
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
            logger.error(f"Error in process_delete_user_id: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_admin_menu())
        finally:
            await state.finish()

    @dp.message_handler(content_types=['text'])
    async def text_menu_handler(message: Message, state: FSMContext):
        logger.info(f"Received text menu command from user {message.from_user.id}: {message.text}")
        try:
            config = Config()
            admin_ids = [id.strip() for id in config.admin_ids.split(',') if id.strip()] if config.admin_ids else []
            is_admin = str(message.from_user.id) in admin_ids

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
            elif is_admin:
                if message.text == "Список ожидающих пользователей":
                    await list_pending_users_command(message)
                elif message.text == "Одобрить пользователя":
                    await message.reply("Введите ID пользователя для одобрения.", reply_markup=get_admin_menu())
                    await AdminState.waiting_for_approve_id.set()
                elif message.text == "Удалить пользователя":
                    await message.reply("Введите ID пользователя для удаления.", reply_markup=get_admin_menu())
                    await AdminState.waiting_for_delete_id.set()
                elif message.text == "Повторно отправить уведомления":
                    await resend_notification_command(message)
                elif message.text == "Тест уведомлений":
                    await debug_notify_command(message)
                elif message.text == "Назад":
                    await message.reply("Возвращение в главное меню.", reply_markup=get_main_menu())
                    await state.finish()
        except Exception as e:
            logger.error(f"Error in text_menu_handler: {e}")
            await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu())
            await state.finish()