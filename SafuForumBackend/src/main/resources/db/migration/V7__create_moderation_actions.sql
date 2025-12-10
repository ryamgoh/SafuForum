CREATE TABLE moderation_actions (
    id BIGSERIAL PRIMARY KEY,
    moderator_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    target_post_id BIGINT REFERENCES posts(id) ON DELETE SET NULL,
    target_comment_id BIGINT REFERENCES comments(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,
    reason TEXT,
    duration_minutes INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_moderation_moderator ON moderation_actions(moderator_id);
CREATE INDEX idx_moderation_target_user ON moderation_actions(target_user_id);
CREATE INDEX idx_moderation_target_post ON moderation_actions(target_post_id);
CREATE INDEX idx_moderation_target_comment ON moderation_actions(target_comment_id);
CREATE INDEX idx_moderation_created ON moderation_actions(created_at DESC);