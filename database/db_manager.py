import psycopg2
from psycopg2.extras import NamedTupleCursor, Json
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
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
                """INSERT INTO users (user_id, username, status)
                VALUES (%s, %s, %s)
                RETURNING user_id""",
                (user_id, username, status)
            )
            user_id = self.cursor.fetchone()[0]
            # Create default notification settings
            self.cursor.execute(
                """INSERT INTO notification_settings (user_id)
                VALUES (%s)""",
                (user_id,)
            )
            self.conn.commit()
            logger.info(f"Added user {user_id} with status {status}")
            return user_id
        except Exception as e:
            logger.error(f"Error in add_user: {e}")
            self.conn.rollback()
            raise

    def get_user(self, user_id: int):
        try:
            self.cursor.execute(
                """SELECT u.*, ns.*
                FROM users u
                LEFT JOIN notification_settings ns ON u.user_id = ns.user_id
                WHERE u.user_id = %s""",
                (user_id,)
            )
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Error in get_user: {e}")
            raise

    def update_user_status(self, user_id: int, status: str):
        try:
            self.cursor.execute(
                """UPDATE users
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s""",
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
                """SELECT user_id AS id, username, status, created_at
                FROM users WHERE status = 'pending'
                ORDER BY created_at ASC"""
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in get_pending_users: {e}")
            raise

    def add_server(self, user_id: int, name: str, address: str, check_type: str, services: Optional[List[Dict]] = None):
        try:
            self.cursor.execute(
                """INSERT INTO servers (user_id, name, address, check_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id""",
                (user_id, name, address, check_type)
            )
            server_id = self.cursor.fetchone()[0]

            # Add services if provided
            if services:
                for service in services:
                    self.cursor.execute(
                        """INSERT INTO server_services
                        (server_id, name, port, description)
                        VALUES (%s, %s, %s, %s)""",
                        (server_id, service['name'], service['port'],
                         service.get('description'))
                    )

            self.conn.commit()
            logger.info(f"Added server {name} for user {user_id}")
            return server_id
        except Exception as e:
            logger.error(f"Error in add_server: {e}")
            self.conn.rollback()
            raise

    def get_user_servers(self, user_id: int):
        try:
            self.cursor.execute(
                """SELECT s.*, array_agg(ss.*) as services
                FROM servers s
                LEFT JOIN server_services ss ON s.id = ss.server_id
                WHERE s.user_id = %s
                GROUP BY s.id
                ORDER BY s.name""",
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

    def update_server_stats(self, server_id: int, stats: Dict):
        try:
            self.cursor.execute(
                """INSERT INTO server_stats
                (server_id, date, uptime_percentage, avg_response_time,
                 total_checks, successful_checks)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (server_id, date)
                DO UPDATE SET
                    uptime_percentage = EXCLUDED.uptime_percentage,
                    avg_response_time = EXCLUDED.avg_response_time,
                    total_checks = EXCLUDED.total_checks,
                    successful_checks = EXCLUDED.successful_checks""",
                (server_id, date.today(), stats['uptime'],
                 stats['avg_response'], stats.get('total_checks', 0),
                 stats.get('successful_checks', 0))
            )
            self.conn.commit()
            logger.info(f"Updated stats for server {server_id}")
        except Exception as e:
            logger.error(f"Error in update_server_stats: {e}")
            self.conn.rollback()
            raise

    def get_server_stats(self, server_id: int, days: int = 7):
        try:
            self.cursor.execute(
                """SELECT *
                FROM server_stats
                WHERE server_id = %s
                AND date >= CURRENT_DATE - interval '%s days'
                ORDER BY date DESC""",
                (server_id, days)
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in get_server_stats: {e}")
            raise

    def update_server_status(self, server_id: int, status: str, last_checked: datetime,
                           response_time: Optional[float] = None,
                           error_message: Optional[str] = None,
                           services_status: Optional[Dict] = None):
        try:
            # Update server status
            self.cursor.execute(
                """UPDATE servers
                SET status = %s, last_checked = %s,
                    response_time = %s, error_message = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s""",
                (status, last_checked, response_time, error_message, server_id)
            )

            # Add to monitoring history
            self.cursor.execute(
                """INSERT INTO monitoring_history
                (server_id, timestamp, status, response_time,
                 error_message, services_status)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (server_id, last_checked, status, response_time,
                 error_message, Json(services_status) if services_status else None)
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