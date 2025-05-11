import psycopg2
from psycopg2.extras import NamedTupleCursor
import logging
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DBManager:
    def __init__(self):
        self.config = Config()
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                cursor_factory=NamedTupleCursor
            )
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def add_user(self, user_id: int, username: str, status: str):
        try:
            self.cursor.execute(
                "INSERT INTO users (user_id, username, status) VALUES (%s, %s, %s)",
                (user_id, username, status)
            )
            self.conn.commit()
            logger.info(f"Added user {user_id} with status {status}")
        except Exception as e:
            logger.error(f"Error in add_user: {e}")
            self.conn.rollback()
            raise

    def get_user(self, user_id: int):
        try:
            self.cursor.execute(
                "SELECT user_id, username, status FROM users WHERE user_id = %s",
                (user_id,)
            )
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Error in get_user: {e}")
            raise

    def update_user_status(self, user_id: int, status: str):
        try:
            self.cursor.execute(
                "UPDATE users SET status = %s WHERE user_id = %s",
                (status, user_id)
            )
            self.conn.commit()
            logger.info(f"Updated user {user_id} status to {status}")
        except Exception as e:
            logger.error(f"Error in update_user_status: {e}")
            self.conn.rollback()
            raise

    def delete_user(self, user_id: int):
        try:
            self.cursor.execute(
                "DELETE FROM users WHERE user_id = %s",
                (user_id,)
            )
            self.conn.commit()
            logger.info(f"Deleted user {user_id}")
        except Exception as e:
            logger.error(f"Error in delete_user: {e}")
            self.conn.rollback()
            raise

    def get_pending_users(self):
        try:
            self.cursor.execute(
                "SELECT user_id AS id, username, status FROM users WHERE status = 'pending'"
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in get_pending_users: {e}")
            raise

    def add_server(self, user_id: int, name: str, address: str, check_type: str):
        try:
            self.cursor.execute(
                "INSERT INTO servers (user_id, name, address, check_type) VALUES (%s, %s, %s, %s)",
                (user_id, name, address, check_type)
            )
            self.conn.commit()
            logger.info(f"Added server {name} for user {user_id}")
        except Exception as e:
            logger.error(f"Error in add_server: {e}")
            self.conn.rollback()
            raise

    def get_user_servers(self, user_id: int):
        try:
            self.cursor.execute(
                "SELECT id, user_id, name, address, check_type, status FROM servers WHERE user_id = %s",
                (user_id,)
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in get_user_servers: {e}")
            raise

    def get_all_servers(self):
        try:
            self.cursor.execute(
                "SELECT id, user_id, name, address, check_type, status, last_checked FROM servers"
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in get_all_servers: {e}")
            raise

    def update_server(self, server_id: int, name: str, address: str, check_type: str):
        try:
            self.cursor.execute(
                "UPDATE servers SET name = %s, address = %s, check_type = %s WHERE id = %s",
                (name, address, check_type, server_id)
            )
            self.conn.commit()
            logger.info(f"Updated server {server_id}")
        except Exception as e:
            logger.error(f"Error in update_server: {e}")
            self.conn.rollback()
            raise

    def update_server_status(self, server_id: int, status: str, last_checked):
        try:
            self.cursor.execute(
                "UPDATE servers SET status = %s, last_checked = %s WHERE id = %s",
                (status, last_checked, server_id)
            )
            self.conn.commit()
            logger.info(f"Updated server {server_id} status to {status}")
        except Exception as e:
            logger.error(f"Error in update_server_status: {e}")
            self.conn.rollback()
            raise

    def delete_server(self, server_id: int):
        try:
            self.cursor.execute(
                "DELETE FROM servers WHERE id = %s",
                (server_id,)
            )
            self.conn.commit()
            logger.info(f"Deleted server {server_id}")
        except Exception as e:
            logger.error(f"Error in delete_server: {e}")
            self.conn.rollback()
            raise

    def add_notification(self, server_id: int, user_id: int, status: str, timestamp):
        try:
            self.cursor.execute(
                "INSERT INTO notifications (server_id, user_id, status, timestamp) VALUES (%s, %s, %s, %s)",
                (server_id, user_id, status, timestamp)
            )
            self.conn.commit()
            logger.info(f"Added notification for server {server_id} and user {user_id}")
        except Exception as e:
            logger.error(f"Error in add_notification: {e}")
            self.conn.rollback()
            raise

    def get_last_notification_time(self):
        try:
            self.cursor.execute(
                "SELECT last_notification FROM notification_cooldown WHERE id = 1"
            )
            result = self.cursor.fetchone()
            return result.last_notification if result else None
        except Exception as e:
            logger.error(f"Error in get_last_notification_time: {e}")
            raise

    def update_notification_time(self, timestamp):
        try:
            self.cursor.execute(
                """
                INSERT INTO notification_cooldown (id, last_notification)
                VALUES (1, %s)
                ON CONFLICT (id) DO UPDATE
                SET last_notification = EXCLUDED.last_notification
                """,
                (timestamp,)
            )
            self.conn.commit()
            logger.info("Updated notification cooldown timestamp")
        except Exception as e:
            logger.error(f"Error in update_notification_time: {e}")
            self.conn.rollback()
            raise