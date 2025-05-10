from aiogram import Dispatcher
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['monitor'])
    async def monitor_command(message: Message):
        logger.info(f"Received /monitor from user {message.from_user.id}")
        try:
            await message.reply("Monitoring status (placeholder).")
        except Exception as e:
            logger.error(f"Error in monitor_command: {e}")
            await message.reply("An error occurred.")