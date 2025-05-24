import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext
from database.db_manager import DBManager
from config.config import Config

@pytest.fixture
async def mock_config():
    config = AsyncMock(spec=Config)
    config.bot_token.get_secret_value.return_value = "12345:ABCDE"
    config.admin_ids = [12345]
    config.database.host = "localhost"
    config.database.port = 5432
    config.database.name = "test_db"
    config.database.user = "test_user"
    config.database.password.get_secret_value.return_value = "test_pass"
    config.monitoring.interval = 60
    return config

@pytest.fixture
async def mock_message():
    message = AsyncMock(spec=Message)
    message.from_user = AsyncMock(spec=User)
    message.from_user.id = 12345
    message.from_user.username = "test_user"
    message.chat = AsyncMock(spec=Chat)
    message.chat.id = 12345
    message.reply = AsyncMock()
    message.bot = AsyncMock()
    message.bot.send_message = AsyncMock()
    return message

@pytest.fixture
async def mock_db():
    db = AsyncMock(spec=DBManager)
    db.get_user = AsyncMock(return_value=None)
    db.add_user = AsyncMock(return_value=12345)
    db.update_user_status = AsyncMock()
    db.get_user_servers = AsyncMock(return_value=[])
    db.add_server = AsyncMock(return_value=1)
    db.update_server = AsyncMock()
    db.delete_server = AsyncMock()
    db.update_server_status = AsyncMock()
    db.get_pending_users = AsyncMock(return_value=[])
    db.delete_user = AsyncMock()
    db.clear_notifications = AsyncMock()
    db.get_all_servers = AsyncMock(return_value=[])
    db.update_server_stats = AsyncMock()
    db.get_server_stats = AsyncMock(return_value=[])
    db.add_notification = AsyncMock()
    db.get_last_notification_time = AsyncMock(return_value=None)
    db.update_notification_time = AsyncMock()
    return db

@pytest.fixture
async def mock_state():
    state = AsyncMock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    state.set_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.clear = AsyncMock()
    return state