import os
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

from utils.logger import setup_logger

logger = setup_logger(__name__)

load_dotenv()


class DatabaseSettings(BaseModel):
    """Настройки подключения к базе данных"""

    host: str = Field(default="localhost", description="Хост базы данных")
    port: int = Field(default=5432, description="Порт базы данных")
    name: str = Field(default="server_monitoring", description="Имя базы данных")
    user: str = Field(default="monitor_user", description="Пользователь базы данных")
    password: str = Field(description="Пароль для доступа к базе данных")
    pool_min_size: int = Field(default=1, description="Минимальный размер пула соединений")
    pool_max_size: int = Field(default=10, description="Максимальный размер пула соединений")

    @validator("port")
    def validate_port(cls, v):
        """Проверка корректности номера порта"""
        if not 1 <= v <= 65535:
            raise ValueError("Порт должен быть в диапазоне от 1 до 65535")
        return v


class MonitoringSettings(BaseModel):
    """Настройки мониторинга серверов"""

    interval: int = Field(default=60, description="Интервал проверки в секундах")
    cooldown_period: int = Field(
        default=20, description="Период задержки между уведомлениями в секундах"
    )
    http_timeout: int = Field(default=5, description="Таймаут HTTP запросов в секундах")
    tcp_timeout: float = Field(default=2.0, description="Таймаут TCP соединения в секундах")
    max_retries: int = Field(default=3, description="Максимальное количество попыток повтора")
    retry_delay: float = Field(default=1.0, description="Задержка между попытками в секундах")
    dns_cache_ttl: int = Field(default=300, description="Время жизни DNS кэша в секундах")
    connection_pool_size: int = Field(default=100, description="Размер пула HTTP соединений")

    @validator("interval", "cooldown_period", "http_timeout", "max_retries")
    def validate_positive_int(cls, v):
        """Проверка положительных целых значений"""
        if v <= 0:
            raise ValueError("Значение должно быть положительным")
        return v

    @validator("tcp_timeout", "retry_delay")
    def validate_positive_float(cls, v):
        """Проверка положительных дробных значений"""
        if v <= 0:
            raise ValueError("Значение должно быть положительным")
        return v


class Config(BaseModel):
    bot_token: str
    admin_ids: List[int] = Field(default_factory=list)
    database: DatabaseSettings
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    @classmethod
    def from_env(cls):
        db_settings = DatabaseSettings(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "server_monitoring"),
            user=os.getenv("DB_USER", "monitor_user"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_min_size=int(os.getenv("DB_POOL_MIN_SIZE", "1")),
            pool_max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
        )

        admin_ids = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

        monitoring_settings = MonitoringSettings(
            interval=int(os.getenv("MONITORING_INTERVAL", "60")),
            cooldown_period=int(os.getenv("COOLDOWN_PERIOD", "20")),
            http_timeout=int(os.getenv("HTTP_TIMEOUT", "5")),
            tcp_timeout=float(os.getenv("TCP_TIMEOUT", "2.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
            dns_cache_ttl=int(os.getenv("DNS_CACHE_TTL", "300")),
            connection_pool_size=int(os.getenv("CONNECTION_POOL_SIZE", "100")),
        )

        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            admin_ids=admin_ids,
            database=db_settings,
            monitoring=monitoring_settings,
        )
