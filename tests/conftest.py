"""Fixtures for tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock()
    config.bot_token = 'test_token'
    config.admin_ids = [12345]
    config.database = MagicMock()
    config.database.host = 'localhost'
    config.database.port = 5432
    config.database.name = 'test_db'
    config.database.user = 'test_user'
    config.database.password = 'test_pass'
    return config

@pytest.fixture
def mock_message():
    """Create a mock message for testing."""
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.username = "test_user"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345
    return message

@pytest.fixture
def mock_db():
    """Create a mock database for testing."""
    db = AsyncMock()
    db.get_user = AsyncMock(return_value=None)
    db.add_user = AsyncMock(return_value=True)
    db.get_server = AsyncMock(return_value=None)
    db.add_server = AsyncMock(return_value=True)
    db.close = AsyncMock()
    return db
