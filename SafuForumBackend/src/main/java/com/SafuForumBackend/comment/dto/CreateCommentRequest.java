package com.SafuForumBackend.comment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.List;

@Data
public class CreateCommentRequest {

    @NotNull(message = "Post ID is required")
    private Long postId;

    private Long parentCommentId;

    @NotBlank(message = "Content is required")
    @Size(min = 1, max = 10000, message = "Content must be between 1 and 10000 characters")
    private String content;

    private List<Long> imageIds;
}