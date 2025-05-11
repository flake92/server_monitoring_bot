"""Tests for user handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User
from handlers.user_handlers import start_command, help_command

@pytest.mark.asyncio
async def test_start_command():
    """Test start command."""
    # Подготовка тестовых данных
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.username = "test_user"

    # Мокаем базу данных
    with patch('handlers.user_handlers.DBManager') as mock_db:
        mock_db_instance = mock_db.return_value
        mock_db_instance.get_user.return_value = None
        
        # Вызываем тестируемую функцию
        await start_command(message)
        
        # Проверяем, что сообщение было отправлено
        message.reply.assert_called_once()
        assert "Добро пожаловать" in message.reply.call_args[0][0]

@pytest.mark.asyncio
async def test_help_command():
    """Test help command."""
    # Подготовка тестовых данных
    message = AsyncMock(spec=Message)
    
    # Вызываем тестируемую функцию
    await help_command(message)
    
    # Проверяем, что сообщение было отправлено
    message.reply.assert_called_once()
    assert "Список доступных команд" in message.reply.call_args[0][0]
