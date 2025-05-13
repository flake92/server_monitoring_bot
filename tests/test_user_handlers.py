"""Tests for user handlers."""

from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

import pytest
from aiogram.types import Message, User

from handlers.user_handlers import help_command, start_command


@dataclass
class TestUser:
    id: int
    username: str
    status: str = 'approved'


@pytest.mark.asyncio
async def test_start_command(mock_message, mock_db, mock_config):
    """Test start command."""
    # Настраиваем моки
    mock_message.reply = AsyncMock()
    mock_db.get_user = AsyncMock(return_value=None)
    mock_db.add_user = AsyncMock(return_value=True)
    mock_db.close = AsyncMock()

    with patch("handlers.user_handlers.DBManager", return_value=mock_db),\
         patch("handlers.user_handlers.Config", return_value=mock_config):
        # Вызываем тестируемую функцию
        await start_command(mock_message)

        # Проверяем, что сообщение было отправлено
        mock_message.reply.assert_called_once()
        assert "Ваша заявка на регистрацию принята" in mock_message.reply.call_args[0][0]
        # Проверяем, что пользователь был добавлен в базу
        mock_db.get_user.assert_called_once_with(mock_message.from_user.id)
        mock_db.add_user.assert_called_once()


@pytest.mark.asyncio
async def test_help_command(mock_message, mock_config):
    """Test help command."""
    # Настраиваем моки
    mock_message.reply = AsyncMock()

    with patch("handlers.user_handlers.Config", return_value=mock_config):
        # Вызываем тестируемую функцию
        await help_command(mock_message)

        # Проверяем, что сообщение было отправлено
        mock_message.reply.assert_called_once()
        assert "Список доступных команд" in mock_message.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_start_command_existing_user(mock_message, mock_db, mock_config):
    """Test start command with existing user."""
    # Настраиваем моки
    mock_message.reply = AsyncMock()
    mock_db.get_user = AsyncMock(return_value=TestUser(id=12345, username="test_user", status="approved"))
    mock_db.add_user = AsyncMock(return_value=True)
    mock_db.close = AsyncMock()

    with patch("handlers.user_handlers.DBManager", return_value=mock_db),\
         patch("handlers.user_handlers.Config", return_value=mock_config):
        # Вызываем тестируемую функцию
        await start_command(mock_message)

        # Проверяем, что сообщение было отправлено
        mock_message.reply.assert_called_once()
        assert "Добро пожаловать" in mock_message.reply.call_args[0][0]
        # Проверяем, что пользователь не был добавлен повторно
        mock_db.get_user.assert_called_once_with(mock_message.from_user.id)
        mock_db.add_user.assert_not_called()
