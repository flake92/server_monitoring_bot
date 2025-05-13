"""Tests for user handlers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from handlers.user_handlers import help_command, start_command


@pytest.mark.asyncio
async def test_start_command(mock_message, mock_db):
    """Test start command."""
    with patch("handlers.user_handlers.DBManager", return_value=mock_db):
        # Вызываем тестируемую функцию
        await start_command(mock_message)

        # Проверяем, что сообщение было отправлено
        mock_message.reply.assert_called_once()
        assert "Добро пожаловать" in mock_message.reply.call_args[0][0]
        # Проверяем, что пользователь был добавлен в базу
        mock_db.get_user.assert_called_once_with(mock_message.from_user.id)
        mock_db.add_user.assert_called_once()


@pytest.mark.asyncio
async def test_help_command(mock_message):
    """Test help command."""
    # Вызываем тестируемую функцию
    await help_command(mock_message)

    # Проверяем, что сообщение было отправлено
    mock_message.reply.assert_called_once()
    assert "Список доступных команд" in mock_message.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_start_command_existing_user(mock_message, mock_db):
    """Test start command with existing user."""
    # Настраиваем мок для существующего пользователя
    mock_db.get_user.return_value = {"id": 12345, "username": "test_user"}

    with patch("handlers.user_handlers.DBManager", return_value=mock_db):
        # Вызываем тестируемую функцию
        await start_command(mock_message)

        # Проверяем, что сообщение было отправлено
        mock_message.reply.assert_called_once()
        assert "С возвращением" in mock_message.reply.call_args[0][0]
        # Проверяем, что пользователь не был добавлен повторно
        mock_db.get_user.assert_called_once_with(mock_message.from_user.id)
        mock_db.add_user.assert_not_called()
