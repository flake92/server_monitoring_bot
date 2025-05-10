from aiogram import Dispatcher
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['admin'])
    async def admin_command(message: Message):
        logger.info(f"Received /admin from user {message.from_user.id}")
        try:
            await message.reply("Admin panel (placeholder).")
        except Exception as e:
            logger.error(f"Error in admin_command: {e}")
            await message.reply("An error occurred.")