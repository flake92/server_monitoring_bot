import asyncpg
from config.config import Config
from database.models import User, Server, ServerStatus, Notification
from typing import List, Optional

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def add_user(self, user: User) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_name, status)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user.user_id, user.username, user.first_name, user.last_name, user.status
            )

    async def get_user(self, user_id: int) -> Optional[User]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1", user_id
            )
            if row:
                return User(**row)
            return None

    async def update_user_status(self, user_id: int, status: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                status, user_id
            )

    async def get_pending_users(self) -> List[User]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users WHERE status = 'pending'"
            )
            return [User(**row) for row in rows]

    async def get_approved_users(self) -> List[User]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users WHERE status = 'approved'"
            )
            return [User(**row) for row in rows]

    async def add_server(self, server: Server) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO servers (user_id, name, address, check_type)
                VALUES ($1, $2, $3, $4)
                """,
                server.user_id, server.name, server.address, server.check_type
            )

    async def get_user_servers(self, user_id: int) -> List[Server]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM servers WHERE user_id = $1", user_id
            )
            return [Server(**row) for row in rows]

    async def get_server(self, server_id: int, user_id: int) -> Optional[Server]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM servers WHERE id = $1 AND user_id = $2",
                server_id, user_id
            )
            if row:
                return Server(**row)
            return None

    async def update_server(self, server_id: int, user_id: int, name: str, address: str, check_type: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE servers
                SET name = $1, address = $2, check_type = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $4 AND user_id = $5
                """,
                name, address, check_type, server_id, user_id
            )

    async def delete_server(self, server_id: int, user_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM servers WHERE id = $1 AND user_id = $2",
                server_id, user_id
            )

    async def get_all_servers(self) -> List[Server]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM servers")
            return [Server(**row) for row in rows]

    async def log_server_status(self, status: ServerStatus) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO server_status (server_id, is_available, checked_at, downtime_start, downtime_end)
                VALUES ($1, $2, $3, $4, $5)
                """,
                status.server_id, status.is_available, status.checked_at,
                status.downtime_start, status.downtime_end
            )

    async def get_last_server_status(self, server_id: int) -> Optional[ServerStatus]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM server_status WHERE server_id = $1 ORDER BY checked_at DESC LIMIT 1",
                server_id
            )
            if row:
                return ServerStatus(**row)
            return None

    async def add_notification(self, notification: Notification) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO notifications (server_id, user_id, message, is_sent)
                VALUES ($1, $2, $3, $4)
                """,
                notification.server_id, notification.user_id,
                notification.message, notification.is_sent
            )

    async def get_unsent_notifications(self) -> List[Notification]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM notifications WHERE is_sent = FALSE"
            )
            return [Notification(**row) for row in rows]

    async def mark_notification_sent(self, notification_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE notifications SET is_sent = TRUE WHERE id = $1",
                notification_id
            )