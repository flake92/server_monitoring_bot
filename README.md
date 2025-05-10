Telegram Server Monitoring Bot 🚀
  
📖 Описание
Telegram Server Monitoring Bot — это модульный Telegram бот, разработанный для мониторинга доступности серверов по протоколам ICMP, HTTP и HTTPS. Пользователи могут добавлять, редактировать, удалять и просматривать свои собственные списки серверов после прохождения модерации администратором. Каждый пользователь имеет независимый список серверов, изолированный от других. Бот включает систему уведомлений с 20-секундным периодом охлаждения для предотвращения ложных сообщений о краткосрочной недоступности. Данные хранятся в PostgreSQL, а проект реализован на Python с использованием библиотеки aiogram.

✨ Основные возможности
👤 Для пользователей

Регистрация: Отправка заявки на использование через команду /start.
Модерация: Все новые пользователи проходят проверку администратором.
Управление серверами (после одобрения):
Добавление серверов с указанием названия, адреса и типа проверки (ICMP, HTTP, HTTPS).
Просмотр списка серверов с возможностью редактирования или удаления.
Проверка текущего статуса серверов через интерактивное меню.


Уведомления: Сообщения о недоступности и восстановлении серверов, включающие:
Название сервера
Адрес
Время начала недоступности
Время восстановления


Период охлаждения: Уведомления отправляются только при недоступности более 20 секунд.

👑 Для администраторов

Админ-панель: Доступ через команду /admin для указанных администраторов.
Модерация: Одобрение или отклонение заявок пользователей.
Управление: Просмотр всех одобренных пользователей и их серверов.
Очистка очереди: Сброс неподтвержденных уведомлений.

🔍 Мониторинг

Периодическая проверка серверов (каждую минуту).
Поддержка протоколов: ICMP (ping), HTTP, HTTPS.
Логирование всех проверок в базе данных.
Уведомления о сбоях с учетом периода охлаждения.

🗄️ База данных

Используется PostgreSQL для хранения:
Пользователей (ID, имя, статус)
Серверов (привязанных к пользователям)
Статусов серверов (доступность, время)
Уведомлений (сообщения, статус)


Индексы для оптимизации запросов.


🛠️ Требования



Компонент
Версия/Описание



Операционная система
Linux (Ubuntu 20.04/22.04)


Python
3.9 или выше


PostgreSQL
14 или выше


Telegram Bot Token
Полученный через @BotFather


Интернет
Для Telegram API и проверки серверов



📁 Структура проекта
server_monitoring_bot/
├── config/
│   └── config.py           # Конфигурация бота (токен, БД)
├── database/
│   ├── __init__.py
│   ├── models.py          # Модели данных
│   ├── db_manager.py      # Управление PostgreSQL
│   └── schema.sql         # Схема базы данных
├── handlers/
│   ├── __init__.py
│   ├── user_handlers.py   # Пользовательские команды
│   ├── admin_handlers.py  # Админские команды
│   └── monitoring_handlers.py  # Мониторинг серверов
├── services/
│   ├── __init__.py
│   ├── monitoring.py      # Проверка серверов
│   ├── notification.py    # Уведомления
│   └── cooldown.py        # Период охлаждения
├── utils/
│   ├── __init__.py
│   └── logger.py          # Логирование
├── requirements.txt        # Зависимости
├── main.py                 # Точка входа
└── README.md               # Документация


🐧 Установка и запуск на Linux (Ubuntu)
Следуйте этим шагам для развертывания бота на сервере Ubuntu 20.04/22.04.
1️⃣ Обновление системы
Обновите пакеты системы:
sudo apt update && sudo apt upgrade -y

2️⃣ Установка Python
Убедитесь, что Python 3.9+ установлен:
python3 --version

Если Python отсутствует или версия ниже, установите:
sudo apt install python3.9 python3-pip python3-venv -y

3️⃣ Установка PostgreSQL

Установите PostgreSQL 14:

sudo apt install postgresql postgresql-contrib -y


Проверьте статус службы:

sudo systemctl status postgresql

Активируйте, если не запущена:
sudo systemctl start postgresql
sudo systemctl enable postgresql


Создайте базу данных и пользователя:

sudo -u postgres psql

В psql выполните:
CREATE DATABASE server_monitoring;
CREATE USER monitor_user WITH PASSWORD 'secure_password';
ALTER ROLE monitor_user SET client_encoding TO 'utf8';
ALTER ROLE monitor_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE monitor_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE server_monitoring TO monitor_user;
\q

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
