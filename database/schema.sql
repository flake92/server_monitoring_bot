CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE servers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    check_type VARCHAR(20) NOT NULL CHECK (check_type IN ('icmp', 'http', 'https')),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE server_statuses (
    id SERIAL PRIMARY KEY,
    server_id INTEGER REFERENCES servers(id) ON DELETE CASCADE,
    is_available BOOLEAN NOT NULL,
    message TEXT,
    checked_at TIMESTAMP NOT NULL
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    server_id INTEGER REFERENCES servers(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'sent')),
    created_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP
);

CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_servers_user_id ON servers(user_id);
CREATE INDEX idx_server_statuses_server_id ON server_statuses(server_id);
CREATE INDEX idx_notifications_status ON notifications(status);