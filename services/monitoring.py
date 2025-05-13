import asyncio
import logging
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import dns.resolver
import ping3
from aiohttp import ClientTimeout, TCPConnector

from config.config import Config
from database.db_manager import DBManager
from services.notification import send_notification
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ServerStatus:
    is_online: bool
    response_time: float
    last_checked: datetime
    error_message: Optional[str] = None
    services: Dict[int, bool] = None
    details: Dict[str, Any] = None


class MonitoringService:
    def __init__(self):
        self.status_history: Dict[int, List[ServerStatus]] = {}
        self.alert_cooldown: Dict[int, datetime] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.config = Config()

        # Default settings
        self.http_timeout = ClientTimeout(total=5, connect=2)
        self.tcp_timeout = 2.0
        self.max_retries = 3
        self.retry_delay = 1.0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=self.http_timeout,
            connector=TCPConnector(
                limit=100,  # Connection pool size
                ttl_dns_cache=300,  # DNS cache TTL
                ssl=False,  # Disable SSL verification for internal services
            ),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def resolve_dns(self, host: str) -> Optional[str]:
        try:
            answers = await asyncio.get_event_loop().run_in_executor(
                None, lambda: dns.resolver.resolve(host, "A")
            )
            return str(answers[0]) if answers else None
        except dns.resolver.NXDOMAIN:
            raise ValueError(f"DNS resolution failed: Domain {host} not found")
        except dns.resolver.NoAnswer:
            raise ValueError(f"DNS resolution failed: No DNS records for {host}")
        except Exception as e:
            raise ValueError(f"DNS resolution failed: {str(e)}")

    async def check_port(
        self, host: str, port: int, timeout: float = 2.0
    ) -> Tuple[bool, float, Optional[str]]:
        for attempt in range(self.max_retries):
            try:
                # Resolve DNS first
                ip_address = await self.resolve_dns(host)
                if not ip_address:
                    return False, 0.0, f"Could not resolve DNS for {host}"

                start_time = datetime.now()
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip_address, port), timeout=timeout
                )
                elapsed = (datetime.now() - start_time).total_seconds()
                writer.close()
                await writer.wait_closed()
                return True, elapsed, None

            except asyncio.TimeoutError:
                error = "Connection timed out"
            except ConnectionRefusedError:
                error = "Connection refused"
            except OSError as e:
                error = f"Network error: {str(e)}"
            except Exception as e:
                error = f"Unexpected error: {str(e)}"

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
            else:
                return False, 0.0, error

    async def check_http(
        self, url: str, timeout: Optional[float] = None
    ) -> Tuple[bool, float, Optional[str]]:
        if timeout:
            timeout = ClientTimeout(total=timeout)
        else:
            timeout = self.http_timeout

        for attempt in range(self.max_retries):
            try:
                if not self.session:
                    raise RuntimeError("HTTP client session not initialized")

                start_time = datetime.now()
                async with self.session.get(url, timeout=timeout, allow_redirects=True) as response:
                    elapsed = (datetime.now() - start_time).total_seconds()

                    # Get response details for better diagnostics
                    status = response.status
                    headers = dict(response.headers)
                    content_type = headers.get("content-type", "unknown")
                    server = headers.get("server", "unknown")

                    details = {
                        "status_code": status,
                        "content_type": content_type,
                        "server": server,
                        "headers": headers,
                    }

                    if 200 <= status < 400:
                        return True, elapsed, None, details
                    else:
                        return False, elapsed, f"HTTP {status}", details

            except asyncio.TimeoutError:
                error = "Connection timed out"
            except aiohttp.ClientError as e:
                error = f"HTTP error: {str(e)}"
            except Exception as e:
                error = f"Unexpected error: {str(e)}"

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
            else:
                return False, 0.0, error, None

    async def check_server(self, server) -> ServerStatus:
        services = {}
        error_msg = None
        start_time = datetime.now()

        try:
            if server.check_type == "icmp":
                result = ping3.ping(server.address, timeout=5)
                is_online = result is not None
                response_time = result if is_online else 0.0

            elif server.check_type in ["http", "https"]:
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
            services=services,
        )

        # Update history
        if server.id not in self.status_history:
            self.status_history[server.id] = []
        self.status_history[server.id].append(status)

        # Keep only last 24 hours of history
        cutoff = datetime.now() - timedelta(hours=24)
        self.status_history[server.id] = [
            s for s in self.status_history[server.id] if s.last_checked > cutoff
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
            "avg_response": sum(response_times) / len(response_times) if response_times else 0,
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
                    error_message=status.error_message,
                )

                if monitoring_service.should_send_alert(server.id, new_status != previous_status):
                    await send_notification(bot, server, new_status, config, status)
            db.close()
        except Exception as e:
            logger.error(f"Error in monitoring task: {e}", exc_info=True)

    # Schedule regular monitoring
    scheduler.add_job(
        monitor_servers,
        "interval",
        seconds=config.monitoring_interval,
        id="monitor_servers",
        replace_existing=True,
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
        calculate_daily_stats, "cron", hour=0, minute=0, id="calculate_stats", replace_existing=True
    )

    return monitoring_service
