"""Fixtures for tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat

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
    with pytest.MongoMock() as mongo:
        yield mongo
