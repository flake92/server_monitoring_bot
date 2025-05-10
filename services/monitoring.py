import subprocess
import aiohttp
from ping3 import ping
import logging
from typing import Tuple
from database.models import Server

logger = logging.getLogger(__name__)

class Monitor:
    """Класс для мониторинга серверов."""

    def __init__(self, server: Server):
        self.server = server
        self.host = server.address
        self.type = server.check_type
        self.timeout = 5
        self.retries = 3

    def check(self) -> Tuple[bool, str]:
        """Проверка доступности сервера."""
        if self.type == "icmp":
            return self._check_icmp()
        elif self.type in ["http", "https"]:
            return asyncio.run(self._check_http())
        else:
            logger.error(f"Неподдерживаемый тип мониторинга: {self.type}")
            return False, f"Неподдерживаемый тип мониторинга: {self.type}"

    def _check_icmp(self) -> Tuple[bool, str]:
        """Проверка по ICMP."""
        for attempt in range(self.retries):
            try:
                result = ping(self.host, timeout=self.timeout)
                if result is not None:
                    logger.info(f"ICMP пинг {self.host}: успешен")
                    return True, "Сервер доступен"
                logger.warning(f"ICMP пинг {self.host}: попытка {attempt + 1} не удалась")
            except Exception as e:
                logger.warning(f"ICMP пинг {self.host}: ошибка {str(e)}")
            time.sleep(1)
        logger.error(f"ICMP пинг {self.host}: сервер недоступен")
        return False, "Сервер недоступен"

    async def _check_http(self) -> Tuple[bool, str]:
        """Проверка по HTTP/HTTPS."""
        protocol = "https" if self.type == "https" else "http"
        url = f"{protocol}://{self.host}"
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.retries):
                try:
                    async with session.get(url, timeout=self.timeout) as response:
                        if response.status == 200:
                            logger.info(f"HTTP/HTTPS запрос {url}: успешен")
                            return True, "Сервер доступен"
                        else:
                            logger.warning(f"HTTP/HTTPS запрос {url}: код ответа {response.status}")
                            if attempt == self.retries - 1:
                                return False, f"Сервер вернул код {response.status}"
                except Exception as e:
                    logger.warning(f"HTTP/HTTPS запрос {url}: попытка {attempt + 1} не удалась")
                    if attempt == self.retries - 1:
                        logger.error(f"HTTP/HTTPS запрос {url}: сервер недоступен")
                        return False, f"Сервер недоступен: {str(e)}"
                await asyncio.sleep(1)
        return False, "Неизвестная ошибка"