from database.db_manager import DatabaseManager
from database.models import Notification, Server
from aiogram import Bot
from config.config import Config

class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def queue_notification(self, server: Server, message: str, user_id: int, db: DatabaseManager):
        notification = Notification(
            id=0,
            server_id=server.id,
            user_id=user_id,
            message=message,
            sent_at=datetime.now(),
            is_sent=False
        )
        await db.add_notification(notification)

    async def send_notifications(self, db: DatabaseManager):
        notifications = await db.get_unsent_notifications()
        for notification in notifications:
            try:
                await self.bot.send_message(notification.user_id, notification.message)
                await db.mark_notification_sent(notification.id)
            except Exception as e:
                print(f"Failed to send notification {notification.id}: {e}")