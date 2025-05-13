from dataclasses import dataclass
from datetime import datetime, time
from typing import Any, Dict, List, Optional


@dataclass
class NotificationSettings:
    """Настройки уведомлений пользователя"""

    user_id: int  # ID пользователя
    notify_on_status_change: bool = True  # Уведомлять об изменении статуса
    notify_on_slow_response: bool = False  # Уведомлять о медленном ответе
    slow_response_threshold: float = 1.0  # Порог медленного ответа в секундах
    notification_cooldown_minutes: int = 5  # Период ожидания между уведомлениями в минутах
    quiet_hours_start: Optional[time] = None  # Начало тихого времени
    quiet_hours_end: Optional[time] = None  # Конец тихого времени


@dataclass
class User:
    """Пользователь системы"""

    user_id: int  # ID пользователя в Telegram
    username: str  # Имя пользователя
    status: str  # Статус пользователя (active/blocked)
    created_at: datetime  # Дата создания
    updated_at: datetime  # Дата последнего обновления
    notification_settings: Optional[NotificationSettings] = None  # Настройки уведомлений


@dataclass
class Service:
    """Сервис на сервере"""

    id: int  # Уникальный идентификатор
    server_id: int  # ID сервера
    name: str  # Название сервиса
    port: int  # Порт сервиса
    description: Optional[str] = None  # Описание сервиса
    created_at: Optional[datetime] = None  # Дата создания


@dataclass
class Server:
    """Сервер для мониторинга"""

    id: int  # Уникальный идентификатор
    user_id: int  # ID владельца сервера
    name: str  # Название сервера
    address: str  # Адрес сервера (IP или домен)
    check_type: str  # Тип проверки (http/tcp)
    status: str  # Статус сервера (up/down/unknown)
    last_checked: Optional[datetime]  # Время последней проверки
    response_time: Optional[float] = None  # Время ответа в секундах
    error_message: Optional[str] = None  # Сообщение об ошибке
    created_at: Optional[datetime] = None  # Дата создания
    updated_at: Optional[datetime] = None  # Дата последнего обновления
    services: List[Service] = None  # Список сервисов на сервере


@dataclass
class ServerStats:
    """Статистика сервера"""

    server_id: int  # ID сервера
    date: datetime  # Дата статистики
    uptime_percentage: float
    avg_response_time: float
    total_checks: int
    successful_checks: int
    created_at: datetime


@dataclass
class MonitoringHistory:
    id: int
    server_id: int
    timestamp: datetime
    status: str
    response_time: Optional[float]
    error_message: Optional[str]
    services_status: Optional[Dict[int, bool]]


@dataclass
class Notification:
    id: int
    server_id: int
    user_id: int
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
