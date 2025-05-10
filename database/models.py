from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """Модель пользователя."""
    id: int
    username: Optional[str]
    status: str  # pending, approved, rejected
    created_at: datetime

@dataclass
class Server:
    """Модель сервера."""
    id: int
    user_id: int
    name: str
    address: str
    check_type: str  # icmp, http, https
    created_at: datetime

@dataclass
class ServerStatus:
    """Модель статуса сервера."""
    id: int
    server_id: int
    is_available: bool
    checked_at: datetime
    message: Optional[str]

@dataclass
class Notification:
    """Модель уведомления."""
    id: int
    server_id: int
    user_id: int
    message: str
    status: str  # pending, sent
    created_at: datetime
    sent_at: Optional[datetime]