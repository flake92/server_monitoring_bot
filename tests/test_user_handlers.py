import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext

from handlers.user_handlers import (
    start_command, help_command, add_server_command,
    list_servers_command, edit_server_command, delete_server_command,
    check_servers_command, UserState, AddServerFSM, EditServerFSM
)
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
    db.get_last_notification_time = AsyncMock(return_value=None)
    return db

@pytest.fixture
async def mock_state():
    state = AsyncMock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.clear = AsyncMock()
    return state

@pytest.mark.asyncio
async def test_start_command_new_user(mock_message, mock_db, mock_config, mock_state):
    mock_db.get_user.return_value = None
    await start_command(mock_message, mock_state)
    mock_db.add_user.assert_called_once_with(12345, "test_user", "approved")
    mock_message.reply.assert_called_with("✅ Добро пожаловать, администратор!", reply_markup=mock_message.reply.call_args[1]["reply_markup"])

@pytest.mark.asyncio
async def test_start_command_existing_user(mock_message, mock_db, mock_config, mock_state):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    await start_command(mock_message, mock_state)
    mock_db.add_user.assert_not_called()
    mock_message.reply.assert_called_with("👋 Добро пожаловать!", reply_markup=mock_message.reply.call_args[1]["reply_markup"])

@pytest.mark.asyncio
async def test_help_command(mock_message, mock_config):
    await help_command(mock_message)
    mock_message.reply.assert_called_once()
    assert "Список доступных команд" in mock_message.reply.call_args[0][0]

@pytest.mark.asyncio
async def test_add_server_command(mock_message, mock_db, mock_config, mock_state):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    await add_server_command(mock_message, mock_state)
    mock_state.set_state.assert_called_with(AddServerFSM.address)
    mock_message.reply.assert_called_with(
        "Введите адрес сервера (например, http://example.com:80):",
        reply_markup=mock_message.reply.call_args[1]["reply_markup"]
    )

@pytest.mark.asyncio
async def test_list_servers_command(mock_message, mock_db, mock_config):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    mock_db.get_user_servers.return_value = [
        {"id": 1, "name": "Test Server", "address": "example.com:80", "check_type": "http", "status": "online"}
    ]
    await list_servers_command(mock_message)
    mock_message.reply.assert_called_once()
    assert "🟢 Test Server (ID: 1)" in mock_message.reply.call_args[0][0]

@pytest.mark.asyncio
async def test_edit_server_command(mock_message, mock_db, mock_config, mock_state):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    mock_db.get_user_servers.return_value = [
        {"id": 1, "name": "Test Server", "address": "example.com:80", "check_type": "http", "status": "online"}
    ]
    await edit_server_command(mock_message, mock_state)
    mock_state.set_state.assert_called_with(EditServerFSM.select_server)
    mock_message.reply.assert_called_once()
    assert "🟢 Test Server (ID: 1)" in mock_message.reply.call_args[0][0]

@pytest.mark.asyncio
async def test_delete_server_command(mock_message, mock_db, mock_config, mock_state):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    mock_db.get_user_servers.return_value = [
        {"id": 1, "name": "Test Server", "address": "example.com:80", "check_type": "http", "status": "online"}
    ]
    await delete_server_command(mock_message, mock_state)
    mock_state.set_state.assert_called_with(UserState.DELETE_SERVER.value)
    mock_message.reply.assert_called_once()
    assert "🟢 Test Server (ID: 1)" in mock_message.reply.call_args[0][0]

@pytest.mark.asyncio
async def test_check_servers_command(mock_message, mock_db, mock_config, mock_state):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    mock_db.get_user_servers.return_value = [
        {"id": 1, "name": "Test Server", "address": "example.com:80", "check_type": "http", "status": "online"}
    ]
    await check_servers_command(mock_message, mock_state)
    mock_state.set_state.assert_called_with(UserState.CHECK_SERVER.value)
    mock_message.reply.assert_called_once()
    assert "🟢 Test Server (ID: 1)" in mock_message.reply.call_args[0][0]

@pytest.mark.asyncio
async def test_clear_notifications_command(mock_message, mock_db, mock_config):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    await mock_db.clear_notifications()
    mock_db.clear_notifications.assert_called_once()

@pytest.mark.asyncio
async def test_get_last_notification_time(mock_message, mock_db, mock_config):
    mock_db.get_user.return_value = {"user_id": 12345, "username": "test_user", "status": "approved"}
    await mock_db.get_last_notification_time()
    mock_db.get_last_notification_time.assert_called_once()