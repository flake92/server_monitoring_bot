import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime
from database.models import Server, User, Notification
from utils.logger import setup_logger

logger = setup_logger(__name__)

load_dotenv()

class DBManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'),
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def add_user(self, user_id: int, username: str, status: str = 'pending'):
        try:
            self.cursor.execute(
                "INSERT INTO users (user_id, username, status) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING",
                (user_id, username, status)
            )
            self.conn.commit()
            logger.info(f"User {user_id} added with status {status}")
        except Exception as e:
            logger.error(f"Error in add_user: {e}")
            self.conn.rollback()
            raise

    def get_user(self, user_id: int) -> User:
        try:
            self.cursor.execute("SELECT user_id, username, status FROM users WHERE user_id = %s", (user_id,))
            row = self.cursor.fetchone()
            return User(*row) if row else None
        except Exception as e:
            logger.error(f"Error in get_user: {e}")
            raise

    def update_user_status(self, user_id: int, status: str):
        try:
            self.cursor.execute("UPDATE users SET status = %s WHERE user_id = %s", (status, user_id))
            self.conn.commit()
            logger.info(f"User {user_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Error in update_user_status: {e}")
            self.conn.rollback()
            raise

    def delete_user(self, user_id: int):
        try:
            self.cursor.execute("DELETE FROM servers WHERE user_id = %s", (user_id,))
            self.cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            self.conn.commit()
            logger.info(f"User {user_id} deleted")
        except Exception as e:
            logger.error(f"Error in delete_user: {e}")
            self.conn.rollback()
            raise

    def get_pending_users(self) -> list[User]:
        try:
            self.cursor.execute("SELECT user_id, username, status FROM users WHERE status = 'pending'")
            users = [User(*row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(users)} pending users")
            return users
        except Exception as e:
            logger.error(f"Error in get_pending_users: {e}")
            raise

    def get_approved_users(self) -> list[User]:
        try:
            self.cursor.execute("SELECT user_id, username, status FROM users WHERE status = 'approved'")
            users = [User(*row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(users)} approved users")
            return users
        except Exception as e:
            logger.error(f"Error in get_approved_users: {e}")
            raise

    def add_server(self, user_id: int, name: str, address: str, check_type: str):
        try:
            self.cursor.execute(
                "INSERT INTO servers (user_id, name, address, check_type, status, last_checked) "
                "VALUES (%s, %s, %s, %s, 'unknown', NULL)",
                (user_id, name, address, check_type)
            )
            self.conn.commit()
            logger.info(f"Server {name} added for user {user_id}")
        except Exception as e:
            logger.error(f"Error in add_server: {e}")
            self.conn.rollback()
            raise

    def update_server(self, server_id: int, name: str, address: str, check_type: str):
        try:
            self.cursor.execute(
                "UPDATE servers SET name = %s, address = %s, check_type = %s WHERE id = %s",
                (name, address, check_type, server_id)
            )
            self.conn.commit()
            logger.info(f"Server {server_id} updated")
        except Exception as e:
            logger.error(f"Error in update_server: {e}")
            self.conn.rollback()
            raise

    def delete_server(self, server_id: int):
        try:
            self.cursor.execute("DELETE FROM notifications WHERE server_id = %s", (server_id,))
            self.cursor.execute("DELETE FROM servers WHERE id = %s", (server_id,))
            self.conn.commit()
            logger.info(f"Server {server_id} deleted")
        except Exception as e:
            logger.error(f"Error in delete_server: {e}")
            self.conn.rollback()
            raise

    def get_user_servers(self, user_id: int) -> list[Server]:
        try:
            self.cursor.execute(
                "SELECT id, user_id, name, address, check_type, status, last_checked FROM servers WHERE user_id = %s",
                (user_id,)
            )
            servers = [Server(*row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(servers)} servers for user {user_id}")
            return servers
        except Exception as e:
            logger.error(f"Error in get_user_servers: {e}")
            raise

    def get_all_servers(self) -> list[Server]:
        try:
            self.cursor.execute(
                "SELECT id, user_id, name, address, check_type, status, last_checked FROM servers"
            )
            servers = [Server(*row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(servers)} servers")
            return servers
        except Exception as e:
            logger.error(f"Error in get_all_servers: {e}")
            raise

    def update_server_status(self, server_id: int, status: str, last_checked: datetime):
        try:
            self.cursor.execute(
                "UPDATE servers SET status = %s, last_checked = %s WHERE id = %s",
                (status, last_checked, server_id)
            )
            self.conn.commit()
            logger.info(f"Server {server_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Error in update_server_status: {e}")
            self.conn.rollback()
            raise

    def add_notification(self, server_id: int, user_id: int, status: str, timestamp: datetime):
        try:
            self.cursor.execute(
                "INSERT INTO notifications (server_id, user_id, status, timestamp) VALUES (%s, %s, %s, %s)",
                (server_id, user_id, status, timestamp)
            )
            self.conn.commit()
            logger.info(f"Notification added for server {server_id}")
        except Exception as e:
            logger.error(f"Error in add_notification: {e}")
            self.conn.rollback()
            raise

    def get_pending_notifications(self, server_id: int, status: str) -> list[Notification]:
        try:
            self.cursor.execute(
                "SELECT id, server_id, user_id, status, timestamp FROM notifications "
                "WHERE server_id = %s AND status = %s",
                (server_id, status)
            )
            notifications = [Notification(*row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(notifications)} pending notifications for server {server_id}")
            return notifications
        except Exception as e:
            logger.error(f"Error in get_pending_notifications: {e}")
            raise

    def delete_notification(self, notification_id: int):
        try:
            self.cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            self.conn.commit()
            logger.info(f"Notification {notification_id} deleted")
        except Exception as e:
            logger.error(f"Error in delete_notification: {e}")
            self.conn.rollback()
            raise

    def clear_notifications(self):
        try:
            self.cursor.execute("DELETE FROM notifications")
            self.conn.commit()
            logger.info("All notifications cleared")
        except Exception as e:
            logger.error(f"Error in clear_notifications: {e}")
            self.conn.rollback()
            raise

    def close(self):
        try:
            self.cursor.close()
            self.conn.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error in close: {e}")