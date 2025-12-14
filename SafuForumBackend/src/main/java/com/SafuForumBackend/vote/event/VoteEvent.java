package com.SafuForumBackend.vote.event;

import com.SafuForumBackend.vote.enums.EntityType;

import java.io.Serializable;

public record VoteEvent(
        Long authorId,
        Long entityId,
        EntityType entityType,
        int voteDelta
) implements Serializable {}
