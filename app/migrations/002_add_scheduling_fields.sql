-- Migration: Add scheduling and publication fields
-- Created: 2026-02-08

-- Добавляем поля для планирования публикаций
ALTER TABLE processed_posts 
  ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS publication_status VARCHAR(50) DEFAULT 'NOT_SCHEDULED',
  ADD COLUMN IF NOT EXISTS instagram_post_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS publication_error TEXT;

-- Создаём индекс для быстрого поиска запланированных постов
CREATE INDEX IF NOT EXISTS idx_scheduled_posts 
  ON processed_posts(scheduled_at) 
  WHERE publication_status = 'SCHEDULED';

-- Комментарии
COMMENT ON COLUMN processed_posts.scheduled_at IS 'Запланированное время публикации';
COMMENT ON COLUMN processed_posts.published_at IS 'Фактическое время публикации';
COMMENT ON COLUMN processed_posts.publication_status IS 'NOT_SCHEDULED, SCHEDULED, PUBLISHING, PUBLISHED, FAILED';
COMMENT ON COLUMN processed_posts.instagram_post_id IS 'ID поста в Instagram';
COMMENT ON COLUMN processed_posts.publication_error IS 'Текст ошибки при публикации';
