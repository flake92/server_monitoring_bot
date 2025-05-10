from aiogram import Bot
from database.db_manager import DBManager
import logging
from typing import List
from database.models import Notification

logger = logging.getLogger(__name__)

class NotificationService:
    """Класс для отправки уведомлений."""

    def __init__(self, bot: Bot, db: DBManager):
        self.bot = bot
        self.db = db

    async def send_pending_notifications(self) -> None:
        """Отправка неподтвержденных уведомлений."""
        notifications: List[Notification] = self.db.get_pending_notifications()
        for notification in notifications:
            try:
                await self.bot.send_message(notification.user_id, notification.message)
                self.db.update_notification_status(notification.id, "sent")
                logger.info(f"Уведомление {notification.id} отправлено пользователю {notification.user_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления {notification.id}: {str(e)}")