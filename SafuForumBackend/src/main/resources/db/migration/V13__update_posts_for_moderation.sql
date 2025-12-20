-- V13: Add moderation tracking to the posts table
ALTER TABLE posts 
    ADD COLUMN status moderation_status NOT NULL DEFAULT 'pending',
    ADD COLUMN version integer NOT NULL DEFAULT 1;

-- Index to help the moderation service find pending content quickly
CREATE INDEX idx_posts_moderation_status ON posts(status);