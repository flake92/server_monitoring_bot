from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)


def is_cooldown_passed(
    last_notification_time: datetime, current_time: datetime, cooldown_period: int
) -> bool:
    try:
        return (current_time - last_notification_time).total_seconds() >= cooldown_period
    except Exception as e:
        logger.error(f"Error in is_cooldown_passed: {e}")
        return False
