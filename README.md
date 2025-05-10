## 1. Установка и настройка

### 1.1 Требования
- Python 3.9+
- PostgreSQL 14+
- Telegram Bot Token от @BotFather

### 1.2 Установка PostgreSQL
1. Установка на Ubuntu:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. Создание базы данных и пользователя:
```bash
sudo -u postgres psql
CREATE DATABASE server_monitoring;
CREATE USER monitor_user WITH PASSWORD 'secure_password';
ALTER ROLE monitor_user SET client_encoding TO 'utf8';
ALTER ROLE monitor_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE monitor_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE server_monitoring TO monitor_user;
\q
```

### 1.3 Установка зависимостей
Создайте файл `requirements.txt`:
```
aiogram==2.25.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
aiohttp==3.9.1
ping3==4.0.3
```

Установите зависимости:
```bash
pip install -r requirements.txt
```
Настройте `.env` в корне проекта:
```
BOT_TOKEN=your_bot_token_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=server_monitoring
DB_USER=monitor_user
DB_PASSWORD=secure_password
ADMIN_IDS=123456789,987654321
```