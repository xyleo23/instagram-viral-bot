-- Migration: Add users and author_settings tables
-- Created: 2026-02-09

-- Таблица пользователей (админы бота)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- Таблица персональных настроек авторов Instagram
CREATE TABLE IF NOT EXISTS author_settings (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    min_likes INTEGER NOT NULL DEFAULT 1000,
    max_post_age_days INTEGER NOT NULL DEFAULT 3,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_author_settings_username ON author_settings(username);
CREATE INDEX IF NOT EXISTS idx_author_settings_admin_id ON author_settings(admin_id);
CREATE INDEX IF NOT EXISTS idx_author_settings_is_active ON author_settings(is_active);

COMMENT ON TABLE users IS 'Пользователи бота (админы) по Telegram ID';
COMMENT ON TABLE author_settings IS 'Персональные настройки парсинга для каждого автора Instagram';
