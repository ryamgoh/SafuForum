package com.SafuForumBackend.comment.dto;

import com.SafuForumBackend.image.dto.ImageResponse;
import com.SafuForumBackend.user.dto.UserSummaryResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CommentResponse {
    private Long id;
    private Long postId;
    private String content;
    private UserSummaryResponse author;
    private List<ImageResponse> images;
    private Long parentCommentId;
    private List<CommentResponse> replies; // Nested replies
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private Boolean isDeleted;
}