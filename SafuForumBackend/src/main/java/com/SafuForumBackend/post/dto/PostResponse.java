package com.SafuForumBackend.post.dto;

import com.SafuForumBackend.post.service.PostService;
import com.SafuForumBackend.tag.dto.TagResponse;
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
public class PostResponse {
    private Long id;
    private String title;
    private String content;
    private UserSummaryResponse author;
    private List<PostService.ImageDTO> images;
    private List<TagResponse> tags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private Boolean isDeleted;
    private Integer voteScore;
    private Integer commentCount;
}