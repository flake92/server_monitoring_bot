CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'unknown',
    last_checked TIMESTAMP,
    response_time FLOAT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS server_services (
    id SERIAL PRIMARY KEY,
    server_id INTEGER REFERENCES servers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(server_id, port)
);

CREATE TABLE IF NOT EXISTS server_stats (
    id SERIAL PRIMARY KEY,
    server_id INTEGER REFERENCES servers(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    uptime_percentage FLOAT NOT NULL DEFAULT 0,
    avg_response_time FLOAT NOT NULL DEFAULT 0,
    total_checks INTEGER NOT NULL DEFAULT 0,
    successful_checks INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(server_id, date)
);

CREATE TABLE IF NOT EXISTS monitoring_history (
    id SERIAL PRIMARY KEY,
    server_id INTEGER REFERENCES servers(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    response_time FLOAT,
    error_message TEXT,
    services_status JSONB
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    server_id INTEGER REFERENCES servers(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    details JSONB
);

CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    notify_on_status_change BOOLEAN DEFAULT true,
    notify_on_slow_response BOOLEAN DEFAULT false,
    slow_response_threshold FLOAT DEFAULT 1.0,
    notification_cooldown_minutes INTEGER DEFAULT 5,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Drop old notification_cooldown table as it's replaced by notification_settings
DROP TABLE IF EXISTS notification_cooldown;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_servers_user_id ON servers(user_id);
CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_server_services_server_id ON server_services(server_id);
CREATE INDEX IF NOT EXISTS idx_server_stats_server_id_date ON server_stats(server_id, date);
CREATE INDEX IF NOT EXISTS idx_monitoring_history_server_id ON monitoring_history(server_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_history_timestamp ON monitoring_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_notifications_server_id ON notifications(server_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp);