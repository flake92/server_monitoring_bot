-- Схема базы данных для Telegram бота мониторинга серверов

-- Таблица пользователей
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,                    -- Уникальный Telegram ID пользователя
    username VARCHAR(255),                        -- Имя пользователя (@username)
    first_name VARCHAR(255),                      -- Имя
    last_name VARCHAR(255),                       -- Фамилия
    status VARCHAR(20) DEFAULT 'pending',          -- Статус: pending, approved, rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Время создания записи
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Время последнего обновления
);

-- Таблица серверов, привязанных к пользователям
CREATE TABLE servers (
    id SERIAL PRIMARY KEY,                        -- Уникальный ID сервера
    user_id BIGINT REFERENCES users(user_id),     -- Ссылка на пользователя-владельца
    name VARCHAR(255) NOT NULL,                   -- Название сервера
    address VARCHAR(255) NOT NULL,                -- Адрес сервера (IP или домен)
    check_type VARCHAR(20) NOT NULL,              -- Тип проверки: icmp, http, https
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Время создания записи
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Время последнего обновления
);

-- Таблица статусов серверов
CREATE TABLE server_status (
    id SERIAL PRIMARY KEY,                        -- Уникальный ID записи
    server_id INTEGER REFERENCES servers(id),     -- Ссылка на сервер
    is_available BOOLEAN NOT NULL,                -- Доступность сервера (true/false)
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Время проверки
    downtime_start TIMESTAMP,                     -- Время начала недоступности
    downtime_end TIMESTAMP                        -- Время окончания недоступности
);

-- Таблица уведомлений
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,                        -- Уникальный ID уведомления
    server_id INTEGER REFERENCES servers(id),     -- Ссылка на сервер
    user_id BIGINT REFERENCES users(user_id),     -- Ссылка на пользователя
    message TEXT NOT NULL,                        -- Текст уведомления
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Время создания уведомления
    is_sent BOOLEAN DEFAULT FALSE                 -- Статус отправки
);

-- Индексы для оптимизации запросов
CREATE INDEX idx_users_status ON users(status);                    -- Для быстрого поиска по статусу
CREATE INDEX idx_servers_user_id ON servers(user_id);              -- Для быстрого поиска серверов пользователя
CREATE INDEX idx_server_status_server_id ON server_status(server_id); -- Для быстрого поиска статусов сервера
CREATE INDEX idx_notifications_server_id ON notifications(server_id); -- Для быстрого поиска уведомлений по серверу