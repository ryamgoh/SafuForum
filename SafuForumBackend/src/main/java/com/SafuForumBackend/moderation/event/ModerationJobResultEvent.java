package com.SafuForumBackend.moderation.event;

import com.SafuForumBackend.moderation.enums.ModerationStatus;

public record ModerationJobResultEvent(
        Long moderationJobId,
        Long postId,
        Integer postVersion,
        ModerationStatus status,
        String errorMessage
) {}

