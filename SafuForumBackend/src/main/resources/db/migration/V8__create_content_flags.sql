CREATE TABLE content_flags (
    id BIGSERIAL PRIMARY KEY,
    reporter_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    comment_id BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    flag_type VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    resolved_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP,
    resolution_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT content_flags_target_check CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR
        (post_id IS NULL AND comment_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX idx_content_flags_user_post ON content_flags(reporter_id, post_id) WHERE post_id IS NOT NULL;
CREATE UNIQUE INDEX idx_content_flags_user_comment ON content_flags(reporter_id, comment_id) WHERE comment_id IS NOT NULL;
CREATE INDEX idx_content_flags_status ON content_flags(status);
CREATE INDEX idx_content_flags_post ON content_flags(post_id);
CREATE INDEX idx_content_flags_comment ON content_flags(comment_id);
CREATE INDEX idx_content_flags_reporter ON content_flags(reporter_id);