from typing import Dict
import time
import logging

logger = logging.getLogger(__name__)

class CooldownManager:
    """Класс для управления периодами охлаждения."""

    def __init__(self):
        self.cooldowns: Dict[int, float] = {}

    def set_cooldown(self, server_id: int, duration: float) -> None:
        """Установка периода охлаждения для сервера."""
        self.cooldowns[server_id] = time.time() + duration
        logger.info(f"Период охлаждения установлен для сервера {server_id} на {duration} секунд")

    def is_on_cooldown(self, server_id: int) -> bool:
        """Проверка, находится ли сервер в периоде охлаждения."""
        if server_id in self.cooldowns:
            if time.time() < self.cooldowns[server_id]:
                return True
            else:
                self.clear_cooldown(server_id)
        return False

    def clear_cooldown(self, server_id: int) -> None:
        """Очистка периода охлаждения."""
        if server_id in self.cooldowns:
            del self.cooldowns[server_id]
            logger.info(f"Период охлаждения очищен для сервера {server_id}")