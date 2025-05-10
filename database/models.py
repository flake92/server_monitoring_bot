from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

@dataclass
class Server:
    id: int
    user_id: int
    name: str
    address: str
    check_type: str
    created_at: datetime
    updated_at: datetime

@dataclass
class ServerStatus:
    id: int
    server_id: int
    is_available: bool
    checked_at: datetime
    downtime_start: Optional[datetime]
    downtime_end: Optional[datetime]

@dataclass
class Notification:
    id: int
    server_id: int
    user_id: int
    message: str
    sent_at: datetime
    is_sent: bool