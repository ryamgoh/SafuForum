package com.SafuForumBackend.moderation.entity;

import com.SafuForumBackend.moderation.enums.JobContentType;

public record ModerationJobSpec(
        String sourceField,
        JobContentType contentType,
        String payload) {
}
