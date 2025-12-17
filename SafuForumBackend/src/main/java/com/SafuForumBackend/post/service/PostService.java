package com.SafuForumBackend.post.service;

import com.SafuForumBackend.comment.repository.CommentRepository;
import com.SafuForumBackend.image.dto.ImageResponse;
import com.SafuForumBackend.image.entity.Image;
import com.SafuForumBackend.image.repository.ImageRepository;
import com.SafuForumBackend.post.dto.CreatePostRequest;
import com.SafuForumBackend.post.dto.PostResponse;
import com.SafuForumBackend.post.dto.UpdatePostRequest;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.post.repository.PostRepository;
import com.SafuForumBackend.tag.dto.TagResponse;
import com.SafuForumBackend.tag.entity.Tag;
import com.SafuForumBackend.tag.repository.TagRepository;
import com.SafuForumBackend.user.dto.UserSummaryResponse;
import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.vote.repository.VoteRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
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
    private final VoteRepository voteRepository;
    private final CommentRepository commentRepository;
    private final ImageRepository imageRepository;  // ADDED

    @Transactional
    public PostResponse createPost(CreatePostRequest request, User currentUser) {

        if (request.getImageIds() != null && !request.getImageIds().isEmpty()) {
            validateAndAttachImages(request.getImageIds(), currentUser, null, true);
        }

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

        if (request.getImageIds() != null && !request.getImageIds().isEmpty()) {
            attachImagesToPost(request.getImageIds(), savedPost, currentUser);
        }

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
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<Post> posts = postRepository.findByIsDeletedFalse(pageable);
        return posts.map(this::convertToResponse);
    }

    public Page<PostResponse> getPostsByUser(Long userId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<Post> posts = postRepository.findByAuthorIdAndIsDeletedFalse(userId, pageable);
        return posts.map(this::convertToResponse);
    }

    public Page<PostResponse> getPostsByTag(String tagSlug, int page, int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));

        Tag tag = tagRepository.findBySlug(tagSlug)
                .orElseThrow(() -> new RuntimeException("Tag not found"));

        Page<Post> posts = postRepository.findByTagsContainingAndIsDeletedFalse(tag, pageable);

        return posts.map(this::convertToResponse);
    }

    public Page<PostResponse> getTrendingPosts(int page, int size, int days) {
        Pageable pageable = PageRequest.of(page, size);
        LocalDateTime since = LocalDateTime.now().minusDays(days);
        Page<Post> posts = postRepository.findTrendingPosts(since, pageable);
        return posts.map(this::convertToResponse);
    }

    public Page<PostResponse> getMostDiscussedPosts(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Post> posts = postRepository.findMostDiscussed(pageable);
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

        // Handle images if provided
        if (request.getImageIds() != null) {
            // Detach old images (they become orphaned and will be cleaned up later)
            List<Image> oldImages = imageRepository.findByPostIdOrderByDisplayOrderAsc(post.getId());
            for (Image oldImage : oldImages) {
                oldImage.setPost(null);
                oldImage.setDisplayOrder(null);
                imageRepository.save(oldImage);
            }

            // Validate and attach new images if any provided
            if (!request.getImageIds().isEmpty()) {
                validateAndAttachImages(request.getImageIds(), currentUser, id, false);
                attachImagesToPost(request.getImageIds(), post, currentUser);
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

    // ============ IMAGE HANDLING METHODS ============

    /**
     * Validate image IDs and check permissions before attaching
     */
    private void validateAndAttachImages(List<Long> imageIds, User currentUser, Long postId, boolean isNewPost) {
        if (imageIds.size() > 10) {
            throw new IllegalArgumentException("Cannot attach more than 10 images to a post");
        }

        for (Long imageId : imageIds) {
            Image image = imageRepository.findById(imageId)
                    .orElseThrow(() -> new IllegalArgumentException("Image not found: " + imageId));

            if (!image.getUploader().getId().equals(currentUser.getId())) {
                throw new IllegalArgumentException("You can only attach your own images");
            }

            if (!isNewPost && (image.getPost() != null || image.getComment() != null)) {
                throw new IllegalArgumentException("Image " + imageId + " is already attached to content");
            }

            if (image.isDeleted()) {
                throw new IllegalArgumentException("Cannot attach deleted image: " + imageId);
            }
        }
    }

    /**
     * Attach validated images to a post
     */
    private void attachImagesToPost(List<Long> imageIds, Post post, User currentUser) {
        for (int i = 0; i < imageIds.size(); i++) {
            Long imageId = imageIds.get(i);
            Image image = imageRepository.findById(imageId)
                    .orElseThrow(() -> new IllegalArgumentException("Image not found: " + imageId));

            image.setPost(post);
            image.setDisplayOrder(i + 1); // 1-indexed
            imageRepository.save(image);
        }
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
                        tag.getColor(),
                        null
                ))
                .collect(Collectors.toList());

        Integer voteScore = voteRepository.getPostVoteScore(post.getId());

        Long commentCount = commentRepository.countByPostIdAndIsDeletedFalse(post.getId());

        List<Image> images = imageRepository.findByPostIdOrderByDisplayOrderAsc(post.getId());
        List<ImageResponse> ImageResponses = images.stream()
                .map(img -> new ImageResponse(
                        img.getId(),
                        img.getSeaweedfsUrl(),
                        img.getOriginalFilename(),
                        img.getFileSizeBytes(),
                        img.getMimeType(),
                        img.getDisplayOrder()
                ))
                .collect(Collectors.toList());

        return PostResponse.builder()
                .id(post.getId())
                .title(post.getTitle())
                .content(post.getContent())
                .author(author)
                .tags(tags)
                .images(ImageResponses)
                .createdAt(post.getCreatedAt())
                .updatedAt(post.getUpdatedAt())
                .isDeleted(post.getIsDeleted())
                .voteScore(voteScore)
                .commentCount(commentCount.intValue())
                .build();
    }
}