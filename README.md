# Telegram Server Monitoring Bot 🚀

## 📖 Описание
Telegram Server Monitoring Bot — это современный, мощный инструмент для мониторинга серверов и сервисов через Telegram. Бот поддерживает мониторинг по ICMP, HTTP/HTTPS и TCP портам, предоставляя подробную статистику и аналитику доступности серверов. Каждый пользователь имеет свой изолированный список серверов с гибкими настройками уведомлений. Проект использует PostgreSQL для хранения данных и реализован на Python с использованием современной версии библиотеки aiogram 3.x.

## ✨ Основные возможности

### 👤 Для пользователей

#### 🔐 Регистрация и доступ
- Простая регистрация через команду /start
- Система модерации новых пользователей
- Персональные настройки уведомлений

#### 🖥️ Управление серверами
- Добавление серверов с расширенными параметрами:
  - Название и описание
  - Адрес и тип проверки (ICMP, HTTP/HTTPS)
  - Дополнительные TCP порты для мониторинга
- Интерактивное управление через inline-кнопки
- Группировка серверов по категориям

#### 📊 Мониторинг и статистика
- Детальная информация о состоянии серверов:
  - Текущий статус и время отклика
  - История доступности
  - Графики производительности
  - Статистика аптайма
- Мониторинг дополнительных сервисов по TCP портам

#### 🔔 Умные уведомления
- Гибкая настройка уведомлений:
  - Изменение статуса сервера
  - Превышение времени отклика
  - Тихие часы
  - Настраиваемый период охлаждения
- Информативные сообщения с деталями:
  - Статус основного сервера
  - Состояние дополнительных сервисов
  - Время отклика
  - Подробности ошибок

### 👑 Для администраторов

#### 🎛️ Панель управления
- Расширенная админ-панель через /admin
- Управление пользователями:
  - Модерация новых заявок
  - Просмотр активности
  - Управление правами

#### 📈 Мониторинг системы
- Общая статистика:
  - Количество активных серверов
  - Статистика доступности
  - Нагрузка на систему
- Журналы событий и ошибок

#### ⚙️ Настройка системы
- Управление глобальными параметрами:
  - Интервалы проверок
  - Пороги уведомлений
  - Системные ограничения

### 🔍 Система мониторинга

#### 🔄 Проверки и протоколы
- Гибкая система мониторинга:
  - ICMP (ping) с измерением времени отклика
  - HTTP/HTTPS с проверкой кодов ответа
  - TCP порты для проверки сервисов
- Асинхронные проверки для высокой производительности
- Настраиваемые интервалы для разных типов проверок

#### 📝 Логирование и аналитика
- Подробное журналирование:
  - Статусы проверок
  - Времена отклика
  - Ошибки и предупреждения
- Аналитика доступности:
  - Процент аптайма
  - Среднее время отклика
  - Тренды производительности

### 🗄️ База данных

#### 📊 Структура данных
- Оптимизированная схема PostgreSQL:
  - Пользователи и настройки
  - Серверы и сервисы
  - История мониторинга
  - Статистика и метрики
  - Уведомления и журналы

#### 🔧 Оптимизация
- Эффективное хранение:
  - Оптимизированные индексы
  - Партиционирование таблиц
  - Автоматическая очистка старых данных
- Поддержка JSON для гибких данных
- Транзакционная целостность


## 🛠️ Требования

### 💻 Системные требования

| Компонент | Версия/Описание |
|-----------|------------------|
| ОС | Linux (Ubuntu 20.04/22.04) |
| Python | 3.11 или выше |
| PostgreSQL | 14 или выше |
| Память | Минимум 512MB RAM |
| Процессор | 1+ CPU |

### 📚 Основные зависимости

| Пакет | Версия |
|-------|--------|
| aiogram | 3.3.0 |
| aiohttp | 3.9.1 |
| psycopg2-binary | 2.9.9 |
| ping3 | 4.0.3 |
| APScheduler | 3.10.4 |

### 🔑 Необходимые токены
- Telegram Bot Token (@BotFather)
- Доступ к PostgreSQL
- Сетевой доступ для проверок



## 📁 Структура проекта

```
server_monitoring_bot/
├── config/
│   ├── __init__.py
│   ├── config.py           # Конфигурация бота
│   └── settings.py         # Настройки приложения
├── database/
│   ├── __init__.py
│   ├── models.py          # Модели данных (Pydantic)
│   ├── db_manager.py      # Управление PostgreSQL
│   ├── migrations/        # Миграции схемы
│   └── schema.sql         # Схема базы данных
├── handlers/
│   ├── __init__.py
│   ├── base.py            # Базовые обработчики
│   ├── user/             # Пользовательские обработчики
│   ├── admin/            # Админские обработчики
│   └── callbacks/        # Обработчики кнопок
├── keyboards/
│   ├── __init__.py
│   ├── user.py            # Клавиатуры пользователей
│   └── admin.py           # Клавиатуры админов
├── services/
│   ├── __init__.py
│   ├── monitoring.py      # Сервис мониторинга
│   ├── notification.py    # Сервис уведомлений
│   ├── statistics.py     # Сервис статистики
│   └── scheduler.py      # Планировщик задач
├── utils/
│   ├── __init__.py
│   ├── logger.py          # Настройка логирования
│   ├── helpers.py         # Вспомогательные функции
│   └── decorators.py     # Декораторы
├── tests/                  # Модульные тесты
├── .env.example           # Пример конфигурации
├── requirements.txt       # Зависимости
├── main.py                # Точка входа
└── README.md              # Документация
```


## 🐧 Установка и настройка

### 🔄 Подготовка системы

1. Обновление пакетов:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Установка зависимостей:
```bash
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql-14 \
    postgresql-contrib-14 \
    libpq-dev \
    build-essential \
    git
```

### 💻 Настройка PostgreSQL

1. Запуск и активация:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. Создание базы данных:
```sql
sudo -u postgres psql -c "CREATE DATABASE server_monitoring;"
sudo -u postgres psql -c "CREATE USER monitor_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "ALTER ROLE monitor_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE monitor_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE monitor_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE server_monitoring TO monitor_user;"
```

### 🔧 Настройка проекта

1. Клонирование репозитория:
```bash
git clone https://github.com/yourusername/server_monitoring_bot.git
cd server_monitoring_bot
```

2. Создание виртуального окружения:
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Настройка конфигурации:
```bash
cp .env.example .env
chmod 600 .env
nano .env  # Редактируйте настройки
```

4. Применение миграций:
```bash
python manage.py migrate
```

## 🚀 Установка и запуск

### 📋 Предварительные требования

- Python 3.11 или выше

### 🛠 Установка и настройка окружения

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
```

2. Активируйте виртуальное окружение:
```bash
source venv/bin/activate  # для Linux/macOS
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```
- PostgreSQL 12 или выше
- Git для клонирования репозитория

### 🔧 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/server_monitoring_bot.git
cd server_monitoring_bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # Для Linux/macOS
venv\Scripts\activate    # Для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте базу данных:
```bash
psql -U postgres
CREATE DATABASE server_monitoring;
CREATE USER monitor_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE server_monitoring TO monitor_user;
```

5. Скопируйте файл с примером настроек и отредактируйте его:
```bash
cp .env.example .env
# Отредактируйте .env файл, указав ваши настройки
```

### 🚀 Запуск

1. Запуск в режиме разработки:
```bash
python main.py
```

2. Запуск через systemd (для Linux):
```bash
sudo cp systemd/server_monitoring_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable server_monitoring_bot
sudo systemctl start server_monitoring_bot
```

3. Проверка статуса:
```bash
sudo systemctl status server_monitoring_bot  # Для systemd
# или
tail -f logs/bot.log                        # Просмотр логов
```

2. Запуск в продакшене (systemd):
```bash
sudo nano /etc/systemd/system/server_monitor_bot.service
```

Содержимое файла сервиса:
```ini
[Unit]
Description=Server Monitoring Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
Group=your_group
WorkingDirectory=/path/to/server_monitoring_bot
Environment="PATH=/path/to/server_monitoring_bot/venv/bin"
ExecStart=/path/to/server_monitoring_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl start server_monitor_bot
sudo systemctl enable server_monitor_bot
```

### 📄 Проверка статуса

```bash
sudo systemctl status server_monitor_bot
journalctl -u server_monitor_bot -f  # Просмотр логов
```

Замените secure_password на надежный пароль.
4️⃣ Клонирование проекта

Установите Git:

sudo apt install git -y


Склонируйте репозиторий (или создайте файлы вручную):

git clone <repository_url> server_monitoring_bot
cd server_monitoring_bot

5️⃣ Настройка виртуального окружения

Создайте и активируйте виртуальное окружение:

python3 -m venv venv
source venv/bin/activate


Установите зависимости:

pip install -r requirements.txt

Содержимое requirements.txt:
aiogram==2.25.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
aiohttp==3.9.1
ping3==4.0.3

6️⃣ Настройка конфигурации

Создайте файл .env:

nano .env

Добавьте:
BOT_TOKEN=your_bot_token_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=server_monitoring
DB_USER=monitor_user
DB_PASSWORD=secure_password
ADMIN_IDS=123456789,987654321


BOT_TOKEN: Получите у @BotFather.
DB_PASSWORD: Пароль пользователя PostgreSQL.
ADMIN_IDS: Telegram ID администраторов (узнать через @userinfobot).

Сохраните и закройте (Ctrl+O, Enter, Ctrl+X).

Ограничьте доступ:

chmod 600 .env

7️⃣ Инициализация базы данных
Примените схему:
psql -U monitor_user -d server_monitoring -f database/schema.sql

Введите пароль monitor_user.
8️⃣ Проверка файлов
Убедитесь, что файлы проекта соответствуют структуре:

config/config.py
database/models.py, db_manager.py, schema.sql
handlers/user_handlers.py, admin_handlers.py, monitoring_handlers.py
services/monitoring.py, notification.py, cooldown.py
utils/logger.py
main.py

9️⃣ Запуск бота

Активируйте виртуальное окружение:

source venv/bin/activate


Запустите:

python main.py

Логи будут в bot.log и консоли.
🔟 Фоновое выполнение
Для постоянной работы используйте systemd или screen.
Systemd

Создайте файл службы:

sudo nano /etc/systemd/system/telegram-bot.service

Добавьте:
[Unit]
Description=Telegram Server Monitoring Bot
After=network.target

[Service]
User=<your_username>
WorkingDirectory=/path/to/server_monitoring_bot
ExecStart=/path/to/server_monitoring_bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

Замените <your_username> и /path/to/server_monitoring_bot.

Активируйте:

sudo systemctl daemon-reload
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot


Проверьте:

sudo systemctl status telegram-bot

Screen

Запустите screen:

screen -S bot


Запустите бота:

source venv/bin/activate
python main.py


Отсоединитесь: Ctrl+A, D.
Вернуться: screen -r bot.


📱 Использование
👤 Пользователи

Найдите бота в Telegram.
Отправьте /start для регистрации.
После одобрения:
Добавить сервер: Укажите название, адрес, тип проверки.
Мои сервера: Просмотр, редактирование, удаление.
Проверить статус: Текущая доступность серверов.


Получайте уведомления о сбоях/восстановлении.

👑 Администраторы

Отправьте /admin.
Функции:
Модерация заявок.
Просмотр пользователей и серверов.
Очистка очереди уведомлений.




📜 Логирование

Логи в bot.log и консоли.
Формат: время, уровень, сообщение.
Просмотр:

tail -f bot.log


🛠️ Отладка



Проблема
Решение



Ошибка PostgreSQL
Проверьте статус: sudo systemctl status postgresql. Убедитесь в правильности .env.


Ошибка Telegram API
Проверьте BOT_TOKEN. Убедитесь в доступе к интернету.


Бот не запускается
Убедитесь, что зависимости установлены. Проверьте bot.log.



🧪 Тестирование
Добавьте сервер вручную:
psql -U monitor_user -d server_monitoring
INSERT INTO servers (user_id, name, address, check_type)
VALUES (123456789, 'Test Server', 'example.com', 'https');


🚀 Расширения

Добавить поддержку других протоколов в services/monitoring.py.
Улучшить уведомления (форматирование, графики).
Реализовать удаление пользователей админами.
Создать веб-интерфейс для управления.


📝 Лицензия
Проект распространяется под MIT License. Соблюдайте лицензии библиотек (aiogram, psycopg2, и т.д.).

📬 Контакты

Issues: Создайте issue в репозитории.
Telegram: Свяжитесь с разработчиком.

⭐ Если проект полезен, поставьте звезду на GitHub!
