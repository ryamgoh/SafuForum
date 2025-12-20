-- V12: Define custom types for the moderation pipeline
CREATE TYPE moderation_status AS ENUM ('pending', 'approved', 'rejected', 'failed');
CREATE TYPE job_content_type AS ENUM ('text', 'image');