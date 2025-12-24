package com.SafuForumBackend.vote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class VoteResponse {
    private Long id;
    private Long userId;
    private Long postId;
    private Long commentId;
    private Short voteType;
    private LocalDateTime createdAt;
}