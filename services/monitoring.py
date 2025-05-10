import asyncio
import logging
import ping3
import aiohttp
from datetime import datetime
from database.db_manager import DBManager
from services.notification import send_notification
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def check_server(server):
    try:
        if server.check_type == 'icmp':
            result = ping3.ping(server.address, timeout=5)
            return "онлайн" if result is not None else "офлайн"
        elif server.check_type in ['http', 'https']:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{server.check_type}://{server.address}", timeout=5) as response:
                    return "онлайн" if response.status == 200 else "офлайн"
    except Exception as e:
        logger.error(f"Error checking server {server.name} ({server.address}): {e}")
        return "офлайн"

async def start_monitoring(bot, config: Config):
    logger.info("Starting server monitoring")
    while True:
        try:
            db = DBManager()
            servers = db.get_all_servers()
            for server in servers:
                previous_status = server.status
                new_status = await check_server(server)
                server.last_checked = datetime.now()
                db.update_server_status(server.id, new_status, server.last_checked)
                if new_status != previous_status:
                    await send_notification(bot, server, new_status, config)
            db.close()
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        await asyncio.sleep(config.monitoring_interval)