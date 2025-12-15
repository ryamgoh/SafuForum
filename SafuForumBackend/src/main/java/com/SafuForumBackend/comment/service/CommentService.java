package com.SafuForumBackend.comment.service;

import com.SafuForumBackend.comment.dto.CommentResponse;
import com.SafuForumBackend.comment.dto.CreateCommentRequest;
import com.SafuForumBackend.comment.dto.UpdateCommentRequest;
import com.SafuForumBackend.comment.entity.Comment;
import com.SafuForumBackend.comment.repository.CommentRepository;
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

    @Transactional
    public CommentResponse createComment(CreateCommentRequest request, User currentUser) {
        Post post = postRepository.findById(request.getPostId())
                .orElseThrow(() -> new RuntimeException("Post not found"));

        if (post.getIsDeleted()) {
            throw new RuntimeException("Cannot comment on a deleted post");
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

    private CommentResponse convertToResponse(Comment comment) {
        UserSummaryResponse author = new UserSummaryResponse(
                comment.getAuthor().getId(),
                comment.getAuthor().getUsername(),
                comment.getAuthor().getDisplayName(),
                comment.getAuthor().getAvatarUrl(),
                comment.getAuthor().getReputation()
        );

        return CommentResponse.builder()
                .id(comment.getId())
                .postId(comment.getPost().getId())
                .content(comment.getContent())
                .author(author)
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