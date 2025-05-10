import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from datetime import datetime
import logging
from config.config import Config
from database.models import User, Server, ServerStatus, Notification

logger = logging.getLogger(__name__)

class DBManager:
    """Класс для управления PostgreSQL."""

    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self) -> None:
        """Установка соединения с базой данных."""
        try:
            self.conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                cursor_factory=RealDictCursor
            )
            logger.info("Подключение к PostgreSQL установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {str(e)}")
            raise

    def close(self) -> None:
        """Закрытие соединения."""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с PostgreSQL закрыто")

    def add_user(self, user_id: int, username: Optional[str]) -> None:
        """Добавление пользователя."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, username, status, created_at)
                VALUES (%s, %s, 'pending', %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (user_id, username, datetime.utcnow())
            )
            self.conn.commit()
            logger.info(f"Пользователь {user_id} добавлен")

    def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            result = cur.fetchone()
            return User(**result) if result else None

    def update_user_status(self, user_id: int, status: str) -> None:
        """Обновление статуса пользователя."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET status = %s WHERE id = %s",
                (status, user_id)
            )
            self.conn.commit()
            logger.info(f"Статус пользователя {user_id} обновлен на {status}")

    def get_pending_users(self) -> List[User]:
        """Получение списка пользователей на модерации."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE status = 'pending'")
            return [User(**row) for row in cur.fetchall()]

    def add_server(self, user_id: int, name: str, address: str, check_type: str) -> None:
        """Добавление сервера."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO servers (user_id, name, address, check_type, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, name, address, check_type, datetime.utcnow())
            )
            self.conn.commit()
            logger.info(f"Сервер {name} добавлен для пользователя {user_id}")

   def get_user_servers(self, user_id: List[Server]) -> List[Server]:
        """Получение серверов пользователя."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM servers WHERE user_id = %s", (user_id,))
            return [Server(**row) for row in cur.fetchall()]

    def delete_server(self, server_id: int, user_id: int) -> None:
        """Удаление сервера."""
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM servers WHERE id = %s AND user_id = %s",
                (server_id, user_id)
            )
            self.conn.commit()
            logger.info(f"Сервер {server_id} удален для пользователя {user_id}")

    def add_status(self, server_id: int, is_available: bool, message: Optional[str]) -> None:
        """Добавление статуса сервера."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO server_statuses (server_id, is_available, message, checked_at)
                VALUES (%s, %s, %s, %s)
                """,
                (server_id, is_available, message, datetime.utcnow())
            )
            self.conn.commit()
            logger.info(f"Статус сервера {server_id} добавлен")

    def add_notification(self, server_id: int, user_id: int, message: str) -> None:
        """Добавление уведомления."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO notifications (server_id, user_id, message, status, created_at)
                VALUES (%s, %s, %s, 'pending', %s)
                """,
                (server_id, user_id, message, datetime.utcnow())
            )
            self.conn.commit()
            logger.info(f"Уведомление добавлено для сервера {server_id}")

    def get_pending_notifications(self) -> List[Notification]:
        """Получение неподтвержденных уведомлений."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM notifications WHERE status = 'pending'")
            return [Notification(**row) for row in cur.fetchall()]

    def update_notification_status(self, notification_id: int, status: str) -> None:
        """Обновление статуса уведомления."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE notifications SET status = %s, sent_at = %s WHERE id = %s
                """,
                (status, datetime.utcnow(), notification_id)
            )
            self.conn.commit()
            logger.info(f"Статус уведомления {notification_id} обновлен на {status}")

if __name__ == "__main__":
    db = DBManager()
    try:
        user = db.get_user(123456789)
        print(f"Пользователь: {user}")
    finally:
        db.close()