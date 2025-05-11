from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, List, Dict, Any

@dataclass
class NotificationSettings:
    user_id: int
    notify_on_status_change: bool = True
    notify_on_slow_response: bool = False
    slow_response_threshold: float = 1.0
    notification_cooldown_minutes: int = 5
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None

@dataclass
class User:
    user_id: int
    username: str
    status: str
    created_at: datetime
    updated_at: datetime
    notification_settings: Optional[NotificationSettings] = None

@dataclass
class Service:
    id: int
    server_id: int
    name: str
    port: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Server:
    id: int
    user_id: int
    name: str
    address: str
    check_type: str
    status: str
    last_checked: Optional[datetime]
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    services: List[Service] = None

@dataclass
class ServerStats:
    server_id: int
    date: datetime
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