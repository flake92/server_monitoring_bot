import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Форматтер для структурированного вывода логов в JSON формате"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        # Основные данные лога
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Извлечение дополнительных полей из записи
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                extra_fields[key] = value

        # Добавление сообщения и дополнительных полей
        try:
            # Попытка парсинга сообщения как JSON
            if isinstance(record.msg, str) and record.msg.startswith("{"):
                try:
                    log_data["message"] = json.loads(record.msg)
                except json.JSONDecodeError:
                    log_data["message"] = record.getMessage()
            else:
                log_data["message"] = record.getMessage()
        except Exception:
            log_data["message"] = str(record.msg)

        if extra_fields:
            log_data["extra"] = extra_fields

        # Добавление информации об ошибке, если есть
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data)


def setup_logger(
    name: str,
    log_dir: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10МБ
    backup_count: int = 5,
    level: int = logging.INFO,
) -> logging.Logger:
    """Настройка логгера с ротацией файлов

    Args:
        name: Имя логгера
        log_dir: Путь к директории с логами
        max_bytes: Максимальный размер файла лога
        backup_count: Количество файлов ротации
        level: Уровень логирования

    Returns:
        Настроенный объект логгера
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Очистка существующих обработчиков
    logger.handlers = []

    # Настройка директории для логов
    if not log_dir:
        log_dir = os.path.join(os.path.expanduser("~"), "server_monitoring_bot", "logs")

    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "bot.log")

    try:
        # Создание обработчика с ротацией файлов
        file_handler = RotatingFileHandler(
            filename=log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)

        # Добавление консольного обработчика для разработки
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        logger.info(
            "Logger initialized",
            extra={
                "logger_name": name,
                "log_file": log_file,
                "max_bytes": max_bytes,
                "backup_count": backup_count,
                "level": logging.getLevelName(level),
            },
        )

    except Exception as e:
        print(f"Failed to initialize logger: {str(e)}")
        raise

    return logger
