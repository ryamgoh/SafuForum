package com.SafuForumBackend.user.dto;

public record UserResponse(
        Long id,
        String username,
        String displayName,
        Integer reputation
) {}