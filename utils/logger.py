import logging
import os

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    log_file = '/home/deployer/server_monitoring_bot/bot.log'
    try:
        # Проверка прав на файл
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
            os.chmod(log_file, 0o664)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Добавить консольный вывод для отладки
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.info(f"Logger initialized for {name}")
    except Exception as e:
        print(f"Failed to initialize logger: {str(e)}")
        raise
    return logger