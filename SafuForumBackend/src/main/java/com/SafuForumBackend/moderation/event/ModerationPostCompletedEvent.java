package com.SafuForumBackend.moderation.event;

import com.SafuForumBackend.moderation.enums.ModerationStatus;

public record ModerationPostCompletedEvent(
        Long postId,
        Integer postVersion,
        ModerationStatus status,
        String reason
) {}

