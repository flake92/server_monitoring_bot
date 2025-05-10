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
    def __init__(self, id: int, name: str, ip_address: str, status: str, last_checked: str):
        self.id = id
        self.name = name
        self.ip_address = ip_address
        self.status = status
        self.last_checked = last_checked

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