import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    """Класс для управления конфигурацией бота."""
    
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "server_monitoring")
    DB_USER: str = os.getenv("DB_USER", "monitor_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "secure_password")
    ADMIN_IDS: List[int] = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip().isdigit()]
    
    @classmethod
    def validate(cls) -> None:
        """Валидация конфигурационных данных."""
        if not cls.BOT_TOKEN:
            raise ValueError("Токен бота не указан в .env")
        if not cls.DB_PASSWORD:
            raise ValueError("Пароль базы данных не указан в .env")
        if not cls.ADMIN_IDS:
            raise ValueError("Список ADMIN_IDS не указан или пуст в .env")

if __name__ == "__main__":
    try:
        Config.validate()
        print("Конфигурация успешно проверена")
    except Exception as e:
        print(f"Ошибка конфигурации: {str(e)}")