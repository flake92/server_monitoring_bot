from datetime import datetime, timedelta
from config.config import Config

class CooldownManager:
    def __init__(self):
        self.cooldowns = {}

    def start_cooldown(self, server_id: int):
        self.cooldowns[server_id] = datetime.now()

    async def is_cooldown_valid(self, server_id: int) -> bool:
        if server_id not in self.cooldowns:
            return False
        elapsed = datetime.now() - self.cooldowns[server_id]
        return elapsed.total_seconds() >= Config.COOLDOWN_PERIOD

    def clear_cooldown(self, server_id: int):
        if server_id in self.cooldowns:
            del self.cooldowns[server_id]