package com.SafuForumBackend.vote.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class VoteRequest {

    private Long postId;
    private Long commentId;

    @NotNull(message = "Vote type is required")
    private Short voteType;
}