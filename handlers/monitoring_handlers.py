from aiogram import Router
from database.db_manager import DBManager
from services.monitoring import Monitor
from services.notification import NotificationService
from services.cooldown import CooldownManager
import asyncio
import logging

router = Router()
logger = logging.getLogger(__name__)

async def monitor_servers(db: DBManager, bot, interval: int = 60) -> None:
    """Периодический мониторинг серверов."""
    cooldown = CooldownManager()
    notification_service = NotificationService(bot, db)
    
    while True:
        try:
            servers = []
            for user in db.get_pending_users() + [u for u in db.get_pending_users() if u.status == "approved"]:
                servers.extend(db.get_user_servers(user.id))
            
            for server in servers:
                monitor = Monitor(server)
                is_available, message = monitor.check()
                
                db.add_status(server.id, is_available, message)
                
                if not is_available and not cooldown.is_on_cooldown(server.id):
                    cooldown.set_cooldown(server.id, 20)  # 20 секунд
                    notification_message = (
                        f"Сервер: {server.name}\n"
                        f"Адрес: {server.address}\n"
                        f"Статус: Недоступен\n"
                        f"Сообщение: {message}\n"
                        f"Время: {asyncio.get_event_loop().time()}"
                    )
                    db.add_notification(server.id, server.user_id, notification_message)
                    await notification_service.send_pending_notifications()
                elif is_available and cooldown.is_on_cooldown(server.id):
                    cooldown.clear_cooldown(server.id)
                    notification_message = (
                        f"Сервер: {server.name}\n"
                        f"Адрес: {server.address}\n"
                        f"Статус: Восстановлен\n"
                        f"Время: {asyncio.get_event_loop().time()}"
                    )
                    db.add_notification(server.id, server.user_id, notification_message)
                    await notification_service.send_pending_notifications()
                
            await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"Ошибка мониторинга: {str(e)}")
            await asyncio.sleep(interval)