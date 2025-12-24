package com.SafuForumBackend.moderation.event;

import com.SafuForumBackend.moderation.enums.JobContentType;

public record ModerationJobRequestedEvent(
        Long moderationJobId,
        Long postId,
        Integer postVersion,
        String sourceField,
        JobContentType contentType,
        String payload
) {}

