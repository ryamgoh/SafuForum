package com.SafuForumBackend.moderation.event;

import com.SafuForumBackend.moderation.enums.ModerationStatus;

public record ModerationJobCompletedEvent(
        ModerationStatus status,
        String reason
) {}
