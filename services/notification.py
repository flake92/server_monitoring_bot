from aiogram import Bot
from datetime import datetime
from database.db_manager import DBManager
from services.cooldown import is_cooldown_passed
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def send_notification(bot: Bot, server, status: str, config):
    try:
        db = DBManager()
        user = db.get_user(server.user_id)
        if user.status != 'approved':
            db.close()
            return
        notification_time = datetime.now()
        pending_notifications = db.get_pending_notifications(server.id, status)
        if pending_notifications:
            for notification in pending_notifications:
                if is_cooldown_passed(notification.timestamp, notification_time, config.cooldown_period):
                    await bot.send_message(
                        server.user_id,
                        f"Сервер: {server.name}\n"
                        f"Адрес: {server.address}\n"
                        f"Статус: {'недоступен' if status == 'офлайн' else 'восстановлен'}\n"
                        f"Время: {notification_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    db.delete_notification(notification.id)
        else:
            db.add_notification(server.id, server.user_id, status, notification_time)
        db.close()
    except Exception as e:
        logger.error(f"Error in send_notification for server {server.name}: {e}")