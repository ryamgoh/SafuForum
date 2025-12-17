CREATE TABLE images (
    id BIGSERIAL PRIMARY KEY,
    uploader_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    comment_id BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    display_order INTEGER NOT NULL,
    seaweedfs_fid VARCHAR(255) NOT NULL,
    seaweedfs_url VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(50) NOT NULL,
    upload_status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    CONSTRAINT images_owner_check CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR
        (post_id IS NULL AND comment_id IS NOT NULL)
    )
);

CREATE INDEX idx_images_uploader ON images(uploader_id);
CREATE INDEX idx_images_post ON images(post_id) WHERE post_id IS NOT NULL;
CREATE INDEX idx_images_comment ON images(comment_id) WHERE comment_id IS NOT NULL;
CREATE INDEX idx_images_created ON images(created_at) WHERE deleted_at IS NULL;