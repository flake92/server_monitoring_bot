import aiohttp
from ping3 import ping
from database.models import Server, ServerStatus
from datetime import datetime
from services.cooldown import CooldownManager
from database.db_manager import DatabaseManager

class ServerMonitor:
    def __init__(self, cooldown_manager: CooldownManager):
        self.cooldown_manager = cooldown_manager
        self.session = None

    async def start(self):
        self.session = aiohttp.ClientSession()

    async def stop(self):
        if self.session:
            await self.session.close()

    async def check_server(self, server: Server) -> bool:
        try:
            if server.check_type == "icmp":
                result = ping(server.address, timeout=2)
                return result is not None
            elif server.check_type in ("http", "https"):
                async with self.session.get(
                    f"{server.check_type}://{server.address}",
                    timeout=5
                ) as response:
                    return response.status == 200
        except Exception:
            return False
        return False

    async def monitor_servers(self, db: DatabaseManager, notification_service):
        servers = await db.get_all_servers()
        for server in servers:
            is_available = await self.check_server(server)
            last_status = await db.get_last_server_status(server.id)
            
            status = ServerStatus(
                id=0,
                server_id=server.id,
                is_available=is_available,
                checked_at=datetime.now(),
                downtime_start=None,
                downtime_end=None
            )

            if last_status and last_status.is_available != is_available:
                if not is_available:
                    status.downtime_start = datetime.now()
                    await self.cooldown_manager.start_cooldown(server.id)
                else:
                    if await self.cooldown_manager.is_cooldown_valid(server.id):
                        status.downtime_end = datetime.now()
                        await notification_service.queue_notification(
                            server,
                            f"Сервер {server.name} ({server.address}) восстановлен.\n"
                            f"Начало простоя: {last_status.downtime_start}\n"
                            f"Конец простоя: {status.downtime_end}",
                            server.user_id
                        )
            elif not is_available and await self.cooldown_manager.is_cooldown_valid(server.id):
                await notification_service.queue_notification(
                    server,
                    f"Сервер {server.name} ({server.address}) недоступен.\n"
                    f"Начало простоя: {status.downtime_start or datetime.now()}",
                    server.user_id
                )

            await db.log_server_status(status)