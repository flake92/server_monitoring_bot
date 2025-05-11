import asyncio
import logging
import ping3
import aiohttp
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from database.db_manager import DBManager
from services.notification import send_notification
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ServerStatus:
    is_online: bool
    response_time: float
    last_checked: datetime
    error_message: Optional[str] = None
    services: Dict[int, bool] = None

class MonitoringService:
    def __init__(self):
        self.status_history: Dict[int, List[ServerStatus]] = {}
        self.alert_cooldown: Dict[int, datetime] = {}

    async def check_port(self, host: str, port: int, timeout: float = 2.0) -> Tuple[bool, float]:
        try:
            start_time = datetime.now()
            reader, writer = await asyncio.open_connection(host, port)
            elapsed = (datetime.now() - start_time).total_seconds()
            writer.close()
            await writer.wait_closed()
            return True, elapsed
        except Exception:
            return False, 0.0

    async def check_http(self, url: str, timeout: float = 5.0) -> Tuple[bool, float, Optional[str]]:
        try:
            async with aiohttp.ClientSession() as session:
                start_time = datetime.now()
                async with session.get(url, timeout=timeout, allow_redirects=True) as response:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    return response.status < 400, elapsed, None
        except asyncio.TimeoutError:
            return False, 0.0, "Timeout"
        except aiohttp.ClientError as e:
            return False, 0.0, str(e)

    async def check_server(self, server) -> ServerStatus:
        services = {}
        error_msg = None
        start_time = datetime.now()

        try:
            if server.check_type == 'icmp':
                result = ping3.ping(server.address, timeout=5)
                is_online = result is not None
                response_time = result if is_online else 0.0

            elif server.check_type in ['http', 'https']:
                url = f"{server.check_type}://{server.address}"
                is_online, response_time, error_msg = await self.check_http(url)

                # Check additional services if main check passed
                if is_online and server.services:
                    for service in server.services:
                        service_online, _ = await self.check_port(server.address, service.port)
                        services[service.port] = service_online

            else:
                is_online = False
                response_time = 0.0
                error_msg = "Unsupported check type"

        except Exception as e:
            logger.error(f"Error checking server {server.name} ({server.address}): {e}")
            is_online = False
            response_time = 0.0
            error_msg = str(e)

        status = ServerStatus(
            is_online=is_online,
            response_time=response_time,
            last_checked=datetime.now(),
            error_message=error_msg,
            services=services
        )

        # Update history
        if server.id not in self.status_history:
            self.status_history[server.id] = []
        self.status_history[server.id].append(status)
        
        # Keep only last 24 hours of history
        cutoff = datetime.now() - timedelta(hours=24)
        self.status_history[server.id] = [
            s for s in self.status_history[server.id]
            if s.last_checked > cutoff
        ]

        return status

    def should_send_alert(self, server_id: int, status_changed: bool) -> bool:
        if not status_changed:
            return False

        now = datetime.now()
        if server_id in self.alert_cooldown:
            if now - self.alert_cooldown[server_id] < timedelta(minutes=5):
                return False

        self.alert_cooldown[server_id] = now
        return True

    def get_server_stats(self, server_id: int) -> Dict:
        if server_id not in self.status_history:
            return {"uptime": 0, "avg_response": 0}

        history = self.status_history[server_id]
        if not history:
            return {"uptime": 0, "avg_response": 0}

        total_checks = len(history)
        online_checks = sum(1 for s in history if s.is_online)
        response_times = [s.response_time for s in history if s.is_online]

        return {
            "uptime": (online_checks / total_checks) * 100 if total_checks > 0 else 0,
            "avg_response": sum(response_times) / len(response_times) if response_times else 0
        }

async def schedule_monitoring_tasks(scheduler, bot):
    monitoring_service = MonitoringService()
    config = Config()

    async def monitor_servers():
        try:
            db = DBManager()
            servers = db.get_all_servers()
            for server in servers:
                previous_status = server.status
                status = await monitoring_service.check_server(server)
                
                new_status = "онлайн" if status.is_online else "офлайн"
                db.update_server_status(
                    server.id,
                    new_status,
                    status.last_checked,
                    response_time=status.response_time,
                    error_message=status.error_message
                )

                if monitoring_service.should_send_alert(server.id, new_status != previous_status):
                    await send_notification(bot, server, new_status, config, status)
            db.close()
        except Exception as e:
            logger.error(f"Error in monitoring task: {e}", exc_info=True)

    # Schedule regular monitoring
    scheduler.add_job(
        monitor_servers,
        'interval',
        seconds=config.monitoring_interval,
        id='monitor_servers',
        replace_existing=True
    )

    # Schedule daily stats calculation
    async def calculate_daily_stats():
        try:
            db = DBManager()
            servers = db.get_all_servers()
            for server in servers:
                stats = monitoring_service.get_server_stats(server.id)
                db.update_server_stats(server.id, stats)
            db.close()
        except Exception as e:
            logger.error(f"Error calculating daily stats: {e}", exc_info=True)

    scheduler.add_job(
        calculate_daily_stats,
        'cron',
        hour=0,
        minute=0,
        id='calculate_stats',
        replace_existing=True
    )

    return monitoring_service