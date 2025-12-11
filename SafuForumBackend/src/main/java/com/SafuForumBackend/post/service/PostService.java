package com.SafuForumBackend.post.service;

import com.SafuForumBackend.post.dto.*;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.post.repository.PostRepository;
import com.SafuForumBackend.tag.entity.Tag;
import com.SafuForumBackend.tag.dto.TagResponse;
import com.SafuForumBackend.tag.repository.TagRepository;
import com.SafuForumBackend.user.dto.UserSummaryResponse;
import com.SafuForumBackend.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class PostService {

    private final PostRepository postRepository;
    private final TagRepository tagRepository;

    @Transactional
    public PostResponse createPost(CreatePostRequest request, User currentUser) {
        Post post = Post.builder()
                .title(request.getTitle())
                .content(request.getContent())
                .author(currentUser)
                .build();

        if (request.getTags() != null && !request.getTags().isEmpty()) {
            for (String tagName : request.getTags()) {
                Tag tag = findOrCreateTag(tagName);
                post.addTag(tag);
            }
        }

        Post savedPost = postRepository.save(post);
        return convertToResponse(savedPost);
    }

    public PostResponse getPostById(Long id) {
        Post post = postRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Post not found"));

        if (post.getIsDeleted()) {
            throw new RuntimeException("Post has been deleted");
        }

        return convertToResponse(post);
    }

    public Page<PostResponse> getAllPosts(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Post> posts = postRepository.findByIsDeletedFalseOrderByCreatedAtDesc(pageable);
        return posts.map(this::convertToResponse);
    }

    public Page<PostResponse> getPostsByTag(String tagSlug, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Post> posts = postRepository.findByTagSlug(tagSlug, pageable);
        return posts.map(this::convertToResponse);
    }

    public Page<PostResponse> getPostsByUser(Long userId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Post> posts = postRepository.findByAuthorIdAndIsDeletedFalseOrderByCreatedAtDesc(userId, pageable);
        return posts.map(this::convertToResponse);
    }

    @Transactional
    public PostResponse updatePost(Long id, UpdatePostRequest request, User currentUser) {
        Post post = postRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Post not found"));

        if (!post.getAuthor().getId().equals(currentUser.getId()) && !currentUser.canModerate()) {
            throw new RuntimeException("You don't have permission to edit this post");
        }

        post.setTitle(request.getTitle());
        post.setContent(request.getContent());
        post.setUpdatedAt(LocalDateTime.now());

        post.clearTags();
        if (request.getTags() != null && !request.getTags().isEmpty()) {
            for (String tagName : request.getTags()) {
                Tag tag = findOrCreateTag(tagName);
                post.addTag(tag);
            }
        }

        Post updatedPost = postRepository.save(post);
        return convertToResponse(updatedPost);
    }

    @Transactional
    public void deletePost(Long id, User currentUser) {
        Post post = postRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Post not found"));

        if (!post.getAuthor().getId().equals(currentUser.getId()) && !currentUser.canModerate()) {
            throw new RuntimeException("You don't have permission to delete this post");
        }

        post.setIsDeleted(true);
        postRepository.save(post);
    }

    private Tag findOrCreateTag(String tagName) {
        String slug = tagName.toLowerCase().replaceAll("\\s+", "-");

        return tagRepository.findBySlug(slug)
                .orElseGet(() -> {
                    Tag newTag = Tag.builder()
                            .name(tagName)
                            .slug(slug)
                            .build();
                    return tagRepository.save(newTag);
                });
    }

    private PostResponse convertToResponse(Post post) {
        UserSummaryResponse author = new UserSummaryResponse(
                post.getAuthor().getId(),
                post.getAuthor().getUsername(),
                post.getAuthor().getDisplayName(),
                post.getAuthor().getAvatarUrl(),
                post.getAuthor().getReputation()
        );

        List<TagResponse> tags = post.getTags().stream()
                .map(tag -> new TagResponse(
                        tag.getId(),
                        tag.getName(),
                        tag.getSlug(),
                        tag.getColor()
                ))
                .collect(Collectors.toList());

        return PostResponse.builder()
                .id(post.getId())
                .title(post.getTitle())
                .content(post.getContent())
                .author(author)
                .tags(tags)
                .createdAt(post.getCreatedAt())
                .updatedAt(post.getUpdatedAt())
                .isDeleted(post.getIsDeleted())
                .build();
    }
}