-- V13: Add moderation tracking to the posts table
ALTER TABLE posts 
    ADD COLUMN status moderation_status NOT NULL DEFAULT 'approved',
    ADD COLUMN version integer NOT NULL DEFAULT 1;
    
-- Ensure all existing posts are treated as approved content
UPDATE posts SET status = 'approved' WHERE status IS NULL;
-- New posts should default to pending for moderation
ALTER TABLE posts ALTER COLUMN status SET DEFAULT 'pending';

-- Index to help the moderation service find pending content quickly
CREATE INDEX idx_posts_moderation_status ON posts(status);