package com.SafuForumBackend.moderation.event;

import com.SafuForumBackend.moderation.enums.ModerationStatus;

public record ModerationJobCompletedEvent(
        Long moderationJobId,
        Long postId,
        Integer postVersion,
        ModerationStatus status,
        String reason
) {}

