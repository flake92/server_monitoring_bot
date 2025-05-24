import os
import re
from typing import List

from pydantic import Field, SecretStr, validator
from pydantic_settings import BaseSettings

from utils.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseSettings(BaseSettings):
    """Database connection settings"""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="server_monitoring", description="Database name")
    user: str = Field(default="monitor_user", description="Database user")
    password: SecretStr = Field(description="Database password")
    pool_min_size: int = Field(default=1, description="Minimum connection pool size")
    pool_max_size: int = Field(default=10, description="Maximum connection pool size")

    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    class Config:
        env_prefix = "DB_"

class MonitoringSettings(BaseSettings):
    """Server monitoring settings"""
    interval: int = Field(default=60, description="Check interval in seconds")
    cooldown_period: int = Field(default=20, description="Notification cooldown in seconds")
    http_timeout: int = Field(default=5, description="HTTP request timeout in seconds")
    tcp_timeout: float = Field(default=2.0, description="TCP connection timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    dns_cache_ttl: int = Field(default=300, description="DNS cache TTL in seconds")
    connection_pool_size: int = Field(default=100, description="HTTP connection pool size")

    @validator("interval", "cooldown_period", "http_timeout", "max_retries")
    def validate_positive_int(cls, v):
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @validator("tcp_timeout", "retry_delay")
    def validate_positive_float(cls, v):
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    class Config:
        env_prefix = "MONITORING_"

class Config(BaseSettings):
    bot_token: SecretStr = Field(description="Telegram bot token")
    admin_ids: List[int] = Field(default_factory=list)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    @validator("bot_token")
    def validate_bot_token(cls, v):
        if not re.match(r"^\d+:[\w-]+$", v.get_secret_value()):
            raise ValueError("Invalid bot token format")
        return v

    @validator("admin_ids")
    def validate_admin_ids(cls, v):
        if not all(isinstance(id, int) for id in v):
            raise ValueError("All admin IDs must be integers")
        return v

    class Config:
        env_prefix = ""
        env_nested_delimiter = "__"

    @classmethod
    def from_env(cls):
        admin_ids_raw = os.getenv("ADMIN_IDS", "")
        admin_ids = []
        if admin_ids_raw:
            try:
                admin_ids = [int(id.strip()) for id in admin_ids_raw.split(",") if id.strip()]
            except ValueError as e:
                logger.error(f"Invalid ADMIN_IDS format: {e}")
                raise ValueError("ADMIN_IDS must contain comma-separated integers")
        return cls(admin_ids=admin_ids)