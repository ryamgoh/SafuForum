package com.SafuForumBackend.moderation.event;

/**
 * Minimal job request payload sent to moderation workers.
 *
 * Job identity is carried via AMQP properties:
 * - correlation_id = moderationJobId
 */
public record ModerationJobRequestedEvent(
        String payload
) {}
