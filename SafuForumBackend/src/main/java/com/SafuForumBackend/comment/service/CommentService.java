package com.SafuForumBackend.comment.service;

import com.SafuForumBackend.comment.dto.CommentResponse;
import com.SafuForumBackend.comment.dto.CreateCommentRequest;
import com.SafuForumBackend.comment.dto.UpdateCommentRequest;
import com.SafuForumBackend.comment.entity.Comment;
import com.SafuForumBackend.comment.repository.CommentRepository;
import com.SafuForumBackend.image.dto.ImageResponse;
import com.SafuForumBackend.image.entity.Image;
import com.SafuForumBackend.image.repository.ImageRepository;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.post.repository.PostRepository;
import com.SafuForumBackend.user.dto.UserSummaryResponse;
import com.SafuForumBackend.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CommentService {

    private final CommentRepository commentRepository;
    private final PostRepository postRepository;
    private final ImageRepository imageRepository;  // ADDED

    @Transactional
    public CommentResponse createComment(CreateCommentRequest request, User currentUser) {
        Post post = postRepository.findById(request.getPostId())
                .orElseThrow(() -> new RuntimeException("Post not found"));

        if (post.getIsDeleted()) {
            throw new RuntimeException("Cannot comment on a deleted post");
        }

        if (request.getImageIds() != null && !request.getImageIds().isEmpty()) {
            validateAndAttachImages(request.getImageIds(), currentUser, null, true);
        }

        Comment comment = Comment.builder()
                .post(post)
                .author(currentUser)
                .content(request.getContent())
                .build();

        if (request.getParentCommentId() != null) {
            Comment parentComment = commentRepository.findById(request.getParentCommentId())
                    .orElseThrow(() -> new RuntimeException("Parent comment not found"));

            if (parentComment.getIsDeleted()) {
                throw new RuntimeException("Cannot reply to a deleted comment");
            }

            comment.setParentComment(parentComment);
        }

        Comment savedComment = commentRepository.save(comment);

        if (request.getImageIds() != null && !request.getImageIds().isEmpty()) {
            attachImagesToComment(request.getImageIds(), savedComment, currentUser);
        }

        return convertToResponse(savedComment);
    }

    public List<CommentResponse> getCommentsForPost(Long postId) {
        List<Comment> topLevelComments = commentRepository
                .findByPostIdAndParentCommentIsNullAndIsDeletedFalseOrderByCreatedAtAsc(postId);

        return topLevelComments.stream()
                .map(this::convertToResponseWithReplies)
                .collect(Collectors.toList());
    }

    public CommentResponse getCommentById(Long id) {
        Comment comment = commentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Comment not found"));

        if (comment.getIsDeleted()) {
            throw new RuntimeException("Comment has been deleted");
        }

        return convertToResponseWithReplies(comment);
    }

    public List<CommentResponse> getUserComments(Long userId) {
        List<Comment> comments = commentRepository.findByAuthorIdAndIsDeletedFalseOrderByCreatedAtDesc(userId);
        return comments.stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    @Transactional
    public CommentResponse updateComment(Long id, UpdateCommentRequest request, User currentUser) {
        Comment comment = commentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Comment not found"));

        if (!comment.getAuthor().getId().equals(currentUser.getId()) && !currentUser.canModerate()) {
            throw new RuntimeException("You don't have permission to edit this comment");
        }

        comment.setContent(request.getContent());
        comment.setUpdatedAt(LocalDateTime.now());

        // Handle image updates
        if (request.getImageIds() != null) {
            updateCommentImages(comment, request.getImageIds(), currentUser);
        }

        Comment updatedComment = commentRepository.save(comment);
        return convertToResponse(updatedComment);
    }

    @Transactional
    public void deleteComment(Long id, User currentUser) {
        Comment comment = commentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Comment not found"));

        if (!comment.getAuthor().getId().equals(currentUser.getId()) && !currentUser.canModerate()) {
            throw new RuntimeException("You don't have permission to delete this comment");
        }

        comment.setIsDeleted(true);
        commentRepository.save(comment);
    }

    // ============ IMAGE HANDLING METHODS ============

    /**
     * Validate image IDs and check permissions before attaching
     */
    private void validateAndAttachImages(List<Long> imageIds, User currentUser, Long commentId, boolean isNewComment) {
        if (imageIds.size() > 3) {
            throw new IllegalArgumentException("Cannot attach more than 3 images to a comment");
        }

        for (Long imageId : imageIds) {
            Image image = imageRepository.findById(imageId)
                    .orElseThrow(() -> new IllegalArgumentException("Image not found: " + imageId));

            if (!image.getUploader().getId().equals(currentUser.getId())) {
                throw new IllegalArgumentException("You can only attach your own images");
            }

            if (!isNewComment && (image.getPost() != null || image.getComment() != null)) {
                throw new IllegalArgumentException("Image " + imageId + " is already attached to content");
            }

            if (image.isDeleted()) {
                throw new IllegalArgumentException("Cannot attach deleted image: " + imageId);
            }
        }
    }

    /**
     * Attach validated images to a comment
     */
    private void attachImagesToComment(List<Long> imageIds, Comment comment, User currentUser) {
        for (int i = 0; i < imageIds.size(); i++) {
            Long imageId = imageIds.get(i);
            Image image = imageRepository.findById(imageId)
                    .orElseThrow(() -> new IllegalArgumentException("Image not found: " + imageId));

            image.setComment(comment);
            image.setDisplayOrder(i + 1); // 1-indexed
            imageRepository.save(image);
        }
    }

    /**
     * Update images for an existing comment
     * - Detaches images not in the new list
     * - Attaches new images
     * - Updates display order
     */
    private void updateCommentImages(Comment comment, List<Long> newImageIds, User currentUser) {
        // Validate the new image list
        if (newImageIds.size() > 3) {
            throw new IllegalArgumentException("Cannot attach more than 3 images to a comment");
        }

        // Get current images attached to this comment
        List<Image> currentImages = imageRepository.findByCommentIdOrderByDisplayOrderAsc(comment.getId());

        // Detach images that are no longer in the list
        for (Image currentImage : currentImages) {
            if (!newImageIds.contains(currentImage.getId())) {
                // This image should be removed from the comment
                currentImage.setComment(null);
                currentImage.setDisplayOrder(0);
                imageRepository.save(currentImage);
            }
        }

        // Process new images list
        for (int i = 0; i < newImageIds.size(); i++) {
            Long imageId = newImageIds.get(i);
            Image image = imageRepository.findById(imageId)
                    .orElseThrow(() -> new IllegalArgumentException("Image not found: " + imageId));

            // Verify ownership
            if (!image.getUploader().getId().equals(currentUser.getId())) {
                throw new IllegalArgumentException("You can only attach your own images");
            }

            // Check if image is deleted
            if (image.isDeleted()) {
                throw new IllegalArgumentException("Cannot attach deleted image: " + imageId);
            }

            // Check if image is already attached to different content
            if (image.getComment() != null && !image.getComment().getId().equals(comment.getId())) {
                throw new IllegalArgumentException("Image " + imageId + " is already attached to another comment");
            }

            if (image.getPost() != null) {
                throw new IllegalArgumentException("Image " + imageId + " is already attached to a post");
            }

            // Attach or update the image
            image.setComment(comment);
            image.setDisplayOrder(i + 1); // 1-indexed
            imageRepository.save(image);
        }
    }


    private CommentResponse convertToResponse(Comment comment) {
        UserSummaryResponse author = new UserSummaryResponse(
                comment.getAuthor().getId(),
                comment.getAuthor().getUsername(),
                comment.getAuthor().getDisplayName(),
                comment.getAuthor().getAvatarUrl(),
                comment.getAuthor().getReputation()
        );

        // Get images for comment (ADDED)
        List<Image> images = imageRepository.findByCommentIdOrderByDisplayOrderAsc(comment.getId());
        List<ImageResponse> imageResponses = images.stream()
                .map(img -> new ImageResponse(
                        img.getId(),
                        img.getSeaweedfsUrl(),
                        img.getOriginalFilename(),
                        img.getFileSizeBytes(),
                        img.getMimeType(),
                        img.getDisplayOrder()
                ))
                .collect(Collectors.toList());

        return CommentResponse.builder()
                .id(comment.getId())
                .postId(comment.getPost().getId())
                .content(comment.getContent())
                .author(author)
                .images(imageResponses)  // ADDED
                .parentCommentId(comment.getParentComment() != null ? comment.getParentComment().getId() : null)
                .createdAt(comment.getCreatedAt())
                .updatedAt(comment.getUpdatedAt())
                .isDeleted(comment.getIsDeleted())
                .build();
    }

    private CommentResponse convertToResponseWithReplies(Comment comment) {
        CommentResponse response = convertToResponse(comment);

        List<Comment> replies = commentRepository.findByParentCommentIdAndIsDeletedFalseOrderByCreatedAtAsc(comment.getId());

        List<CommentResponse> replyResponses = replies.stream()
                .map(this::convertToResponseWithReplies)
                .collect(Collectors.toList());

        response.setReplies(replyResponses);
        return response;
    }
}