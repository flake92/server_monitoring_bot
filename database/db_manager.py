import logging
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Dict, List, Optional

import asyncpg
from asyncpg import Record

from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DBManager:
    """Asynchronous database manager with connection pooling"""
    _pool = None

    def __init__(self, config: Config):
        self.config = config
        self.pool = None

    async def _ensure_pool(self):
        if DBManager._pool is None:
            try:
                DBManager._pool = await asyncpg.create_pool(
                    host=self.config.database.host,
                    port=self.config.database.port,
                    database=self.config.database.name,
                    user=self.config.database.user,
                    password=self.config.database.password.get_secret_value(),
                    min_size=self.config.database.pool_min_size,
                    max_size=self.config.database.pool_max_size,
                )
                logger.info("Connection pool initialized")
            except Exception as e:
                logger.error(f"Error initializing connection pool: {e}")
                raise

    async def __aenter__(self):
        await self._ensure_pool()
        self.pool = DBManager._pool
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # Pool is managed globally

    @asynccontextmanager
    async def get_connection(self):
        conn = None
        try:
            await self._ensure_pool()
            conn = await DBManager._pool.acquire()
            yield conn
            await conn.execute("COMMIT")
        except Exception as e:
            if conn:
                await conn.execute("ROLLBACK")
            raise e
        finally:
            if conn:
                await DBManager._pool.release(conn)

    async def close(self):
        if DBManager._pool:
            await DBManager._pool.close()
            DBManager._pool = None
            logger.info("Connection pool closed")

    async def add_user(self, user_id: int, username: str, status: str) -> int:
        async with self.get_connection() as conn:
            try:
                user_id = await conn.fetchval(
                    """
                    INSERT INTO users (user_id, username, status)
                    VALUES ($1, $2, $3)
                    RETURNING user_id
                    """,
                    user_id, username, status
                )
                await conn.execute(
                    """
                    INSERT INTO notification_settings (user_id)
                    VALUES ($1)
                    """,
                    user_id
                )
                logger.info(f"Added user {user_id} with status {status}")
                return user_id
            except Exception as e:
                logger.error(f"Error adding user: {e}")
                raise

    async def get_user(self, user_id: int) -> Optional[Record]:
        async with self.get_connection() as conn:
            try:
                return await conn.fetchrow(
                    """
                    SELECT u.*, ns.*
                    FROM users u
                    LEFT JOIN notification_settings ns ON u.user_id = ns.user_id
                    WHERE u.user_id = $1
                    """,
                    user_id
                )
            except Exception as e:
                logger.error(f"Error getting user: {e}")
                raise

    async def update_user_status(self, user_id: int, status: str):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    """
                    UPDATE users
                    SET status = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $2
                    """,
                    status, user_id
                )
                logger.info(f"Updated user {user_id} status to {status}")
            except Exception as e:
                logger.error(f"Error updating user status: {e}")
                raise

    async def delete_user(self, user_id: int):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    "DELETE FROM users WHERE user_id = $1",
                    user_id
                )
                logger.info(f"Deleted user {user_id}")
            except Exception as e:
                logger.error(f"Error deleting user: {e}")
                raise

    async def get_pending_users(self) -> List[Record]:
        async with self.get_connection() as conn:
            try:
                return await conn.fetch(
                    """
                    SELECT user_id AS id, username, status, created_at
                    FROM users WHERE status = 'pending'
                    ORDER BY created_at ASC
                    """
                )
            except Exception as e:
                logger.error(f"Error getting pending users: {e}")
                raise

    async def add_server(
        self,
        user_id: int,
        name: str,
        address: str,
        check_type: str,
        services: Optional[List[Dict]] = None,
    ) -> int:
        async with self.get_connection() as conn:
            try:
                server_id = await conn.fetchval(
                    """
                    INSERT INTO servers (user_id, name, address, check_type)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    user_id, name, address, check_type
                )
                if services:
                    for service in services:
                        await conn.execute(
                            """
                            INSERT INTO server_services (server_id, name, port, description)
                            VALUES ($1, $2, $3, $4)
                            """,
                            server_id, service["name"], service["port"], service.get("description")
                        )
                logger.info(f"Added server {name} for user {user_id}")
                return server_id
            except Exception as e:
                logger.error(f"Error adding server: {e}")
                raise

    async def get_user_servers(self, user_id: int) -> List[Record]:
        async with self.get_connection() as conn:
            try:
                return await conn.fetch(
                    """
                    SELECT s.*, array_agg(ss.*) as services
                    FROM servers s
                    LEFT JOIN server_services ss ON s.id = ss.server_id
                    WHERE s.user_id = $1
                    GROUP BY s.id
                    ORDER BY s.name
                    """,
                    user_id
                )
            except Exception as e:
                logger.error(f"Error getting user servers: {e}")
                raise

    async def get_all_servers(self) -> List[Record]:
        async with self.get_connection() as conn:
            try:
                return await conn.fetch(
                    """
                    SELECT id, user_id, name, address, check_type, status, last_checked
                    FROM servers
                    """
                )
            except Exception as e:
                logger.error(f"Error getting all servers: {e}")
                raise

    async def update_server(self, server_id: int, name: str, address: str, check_type: str):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    """
                    UPDATE servers
                    SET name = $1, address = $2, check_type = $3
                    WHERE id = $4
                    """,
                    name, address, check_type, server_id
                )
                logger.info(f"Updated server {server_id}")
            except Exception as e:
                logger.error(f"Error updating server: {e}")
                raise

    async def update_server_stats(self, server_id: int, stats: Dict):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO server_stats
                    (server_id, date, uptime_percentage, avg_response_time,
                     total_checks, successful_checks)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (server_id, date)
                    DO UPDATE SET
                        uptime_percentage = EXCLUDED.uptime_percentage,
                        avg_response_time = EXCLUDED.avg_response_time,
                        total_checks = EXCLUDED.total_checks,
                        successful_checks = EXCLUDED.successful_checks
                    """,
                    server_id,
                    date.today(),
                    stats["uptime"],
                    stats["avg_response"],
                    stats.get("total_checks", 0),
                    stats.get("successful_checks", 0),
                )
                logger.info(f"Updated stats for server {server_id}")
            except Exception as e:
                logger.error(f"Error updating server stats: {e}")
                raise

    async def get_server_stats(self, server_id: int, days: int = 7) -> List[Record]:
        async with self.get_connection() as conn:
            try:
                return await conn.fetch(
                    """
                    SELECT *
                    FROM server_stats
                    WHERE server_id = $1
                    AND date >= CURRENT_DATE - interval '$2 days'
                    ORDER BY date DESC
                    """,
                    server_id, days
                )
            except Exception as e:
                logger.error(f"Error getting server stats: {e}")
                raise

    async def update_server_status(
        self,
        server_id: int,
        status: str,
        last_checked: datetime,
        response_time: Optional[float] = None,
        error_message: Optional[str] = None,
        services_status: Optional[Dict] = None,
    ):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    """
                    UPDATE servers
                    SET status = $1, last_checked = $2,
                        response_time = $3, error_message = $4,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $5
                    """,
                    status, last_checked, response_time, error_message, server_id
                )
                await conn.execute(
                    """
                    INSERT INTO monitoring_history
                    (server_id, timestamp, status, response_time,
                     error_message, services_status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    server_id, last_checked, status, response_time, error_message, services_status
                )
                logger.info(f"Updated server {server_id} status to {status}")
            except Exception as e:
                logger.error(f"Error updating server status: {e}")
                raise

    async def delete_server(self, server_id: int):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    "DELETE FROM servers WHERE id = $1",
                    server_id
                )
                logger.info(f"Deleted server {server_id}")
            except Exception as e:
                logger.error(f"Error deleting server: {e}")
                raise

    async def add_notification(self, server_id: int, user_id: int, status: str, timestamp: datetime):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO notifications (server_id, user_id, status, timestamp)
                    VALUES ($1, $2, $3, $4)
                    """,
                    server_id, user_id, status, timestamp
                )
                logger.info(f"Added notification for server {server_id} and user {user_id}")
            except Exception as e:
                logger.error(f"Error adding notification: {e}")
                raise

    async def get_last_notification_time(self) -> Optional[datetime]:
        async with self.get_connection() as conn:
            try:
                result = await conn.fetchrow(
                    """
                    SELECT last_notification
                    FROM notification_cooldown
                    WHERE id = 1
                    """
                )
                return result["last_notification"] if result else None
            except Exception as e:
                logger.error(f"Error getting last notification time: {e}")
                raise

    async def update_notification_time(self, timestamp: datetime):
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO notification_cooldown (id, last_notification)
                    VALUES (1, $1)
                    ON CONFLICT (id) DO UPDATE
                    SET last_notification = EXCLUDED.last_notification
                    """,
                    timestamp
                )
                logger.info("Updated notification cooldown timestamp")
            except Exception as e:
                logger.error(f"Error updating notification time: {e}")
                raise

    async def clear_notifications(self):
        async with self.get_connection() as conn:
            try:
                await conn.execute("DELETE FROM notifications")
                logger.info("Notifications cleared")
            except Exception as e:
                logger.error(f"Error clearing notifications: {e}")
                raise