-- Drop the old constraint
ALTER TABLE images DROP CONSTRAINT images_owner_check;

-- Add new constraint that allows orphaned images temporarily
ALTER TABLE images ADD CONSTRAINT images_owner_check CHECK (
    (post_id IS NOT NULL AND comment_id IS NULL) OR
    (post_id IS NULL AND comment_id IS NOT NULL) OR
    (post_id IS NULL AND comment_id IS NULL)
);