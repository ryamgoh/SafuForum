package com.SafuForumBackend.moderation.enums;

/**
 * Enumeration representing the status of a moderation action.
 * - pending: The moderation is still in progress.
 * - approved: The content has been approved by moderation.
 * - rejected: The content has been rejected by moderation.
 * - failed: The moderation process failed due to an error.
 */
public enum ModerationStatus {
    pending,
    approved,
    rejected,
    failed
}
