package com.SafuForumBackend.post.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
import java.util.List;

@Data
public class CreatePostRequest {

    @NotBlank(message = "Title is required")
    @Size(min = 3, max = 300, message = "Title must be between 3 and 300 characters")
    private String title;

    @NotBlank(message = "Content is required")
    @Size(min = 10, message = "Content must be at least 10 characters")
    private String content;

    private List<String> tags;
}