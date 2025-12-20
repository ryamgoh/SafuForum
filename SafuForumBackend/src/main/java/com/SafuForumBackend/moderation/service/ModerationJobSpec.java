package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.enums.JobContentType;

public record ModerationJobSpec(
                String sourceField,
                JobContentType contentType,
                String payload) {
}
