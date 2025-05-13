from datetime import datetime
from typing import Dict, Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.db_manager import DBManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


def format_response_time(response_time: Optional[float]) -> str:
    if response_time is None:
        return "N/A"
    if response_time < 0.1:
        return f"{response_time * 1000:.0f} мс"
    return f"{response_time:.2f} сек"


def should_send_notification(
    settings, status_changed: bool, response_time: Optional[float] = None
) -> bool:
    # Check quiet hours
    now = datetime.now().time()
    if settings.quiet_hours_start and settings.quiet_hours_end:
        if settings.quiet_hours_start <= now <= settings.quiet_hours_end:
            return False

    # Check notification preferences
    if status_changed and settings.notify_on_status_change:
        return True

    if (
        settings.notify_on_slow_response
        and response_time
        and response_time > settings.slow_response_threshold
    ):
        return True

    return False


def create_server_keyboard(server_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{server_id}"),
        InlineKeyboardButton("🔄 Проверить", callback_data=f"check_{server_id}"),
        InlineKeyboardButton("⚙️ Настройки", callback_data=f"settings_{server_id}"),
        InlineKeyboardButton("📝 История", callback_data=f"history_{server_id}"),
    )
    return keyboard


def format_notification_message(server, status: str, server_status) -> str:
    status_emoji = "🟢" if status == "онлайн" else "🔴"
    status_text = "доступен" if status == "онлайн" else "недоступен"

    message = [
        f"<b>{status_emoji} Сервер: {server.name}</b>",
        f"📍 Адрес: <code>{server.address}</code>",
        f"ℹ️ Статус: {status_text}",
        f"⏱ Время отклика: {format_response_time(server_status.response_time)}",
        f"🕒 Проверка: {server_status.last_checked.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if server_status.error_message:
        message.append(f"⚠️ Ошибка: {server_status.error_message}")

    if server_status.services:
        message.append("\n📌 Статус сервисов:")
        for port, is_up in server_status.services.items():
            status_icon = "🟢" if is_up else "🔴"
            service = next((s for s in server.services if s.port == port), None)
            service_name = service.name if service else f"Порт {port}"
            message.append(f"{status_icon} {service_name}")

    return "\n".join(message)


async def send_notification(bot: Bot, server, status: str, config, server_status):
    try:
        db = DBManager()
        user = db.get_user(server.user_id)
        if not user or user.status != "approved":
            db.close()
            return

        notification_time = datetime.now()

        # Check notification settings
        if not should_send_notification(user, status != server.status, server_status.response_time):
            db.close()
            return

        # Format and send message
        message = format_notification_message(server, status, server_status)
        keyboard = create_server_keyboard(server.id)

        sent_message = await bot.send_message(
            server.user_id, message, reply_markup=keyboard, parse_mode="HTML"
        )

        # Record notification
        details = {
            "message_id": sent_message.message_id,
            "response_time": server_status.response_time,
            "error_message": server_status.error_message,
            "services_status": server_status.services,
        }

        db.add_notification(server.id, server.user_id, status, notification_time, details)
        db.close()

    except Exception as e:
        logger.error(f"Error in send_notification for server {server.name}: {e}", exc_info=True)
