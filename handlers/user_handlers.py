from aiogram import Dispatcher
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def start_command(message: Message):
        logger.info(f"Received /start from user {message.from_user.id}")
        try:
            await message.reply("Welcome to Server Monitoring Bot! Use /help to see commands.")
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await message.reply("An error occurred. Please try again later.")

    @dp.message_handler(commands=['help'])
    async def help_command(message: Message):
        logger.info(f"Received /help from user {message.from_user.id}")
        await message.reply("Available commands:\n/start - Start the bot\n/help - Show this help")