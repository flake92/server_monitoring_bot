from datetime import datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator

class NotificationSettings(BaseModel):
    """User notification settings"""
    user_id: int
    notify_on_status_change: bool = True
    notify_on_slow_response: bool = False
    slow_response_threshold: float = 1.0
    notification_cooldown_minutes: int = 5
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None

    @validator("slow_response_threshold", "notification_cooldown_minutes")
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

class User(BaseModel):
    """System user"""
    user_id: int
    username: str
    status: str
    created_at: datetime
    updated_at: datetime
    notification_settings: Optional[NotificationSettings] = None

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["pending", "approved", "blocked"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class Service(BaseModel):
    """Server service"""
    id: int
    server_id: int
    name: str
    port: int
    description: Optional[str] = None

    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

class Server(BaseModel):
    """Server for monitoring"""
    id: int
    user_id: int
    name: str
    address: str
    check_type: str
    status: str
    last_checked: Optional[datetime] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    services: Optional[List[Service]] = None

    @validator("check_type")
    def validate_check_type(cls, v):
        valid_types = ["icmp", "http", "https", "tcp"]
        if v not in valid_types:
            raise ValueError(f"check_type must be one of {valid_types}")
        return v

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["online", "offline", "unknown"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class ServerStats(BaseModel):
    """Server statistics"""
    server_id: int
    date: datetime
    uptime_percentage: float
    avg_response_time: float
    total_checks: int
    successful_checks: int

    @validator("uptime_percentage")
    def validate_uptime(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Uptime percentage must be between 0 and 100")
        return v

class MonitoringHistory(BaseModel):
    """Monitoring history record"""
    id: int
    server_id: int
    timestamp: datetime
    status: str
    response_time: Optional[float]
    error_message: Optional[str]
    services_status: Optional[Dict[int, bool]]

class Notification(BaseModel):
    """Notification record"""
    id: int
    server_id: int
    user_id: int
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None