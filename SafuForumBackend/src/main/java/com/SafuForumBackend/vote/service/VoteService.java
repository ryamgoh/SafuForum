package com.SafuForumBackend.vote.service;

import com.SafuForumBackend.comment.entity.Comment;
import com.SafuForumBackend.comment.repository.CommentRepository;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.post.repository.PostRepository;
import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.vote.dto.VoteRequest;
import com.SafuForumBackend.vote.dto.VoteResponse;
import com.SafuForumBackend.vote.dto.VoteScoreResponse;
import com.SafuForumBackend.vote.entity.Vote;
import com.SafuForumBackend.vote.repository.VoteRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class VoteService {

    private final VoteRepository voteRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;

    @Transactional
    public VoteResponse vote(VoteRequest request, User currentUser) {
        if ((request.getPostId() == null && request.getCommentId() == null) ||
                (request.getPostId() != null && request.getCommentId() != null)) {
            throw new RuntimeException("Must specify either postId or commentId, not both");
        }

        if (request.getVoteType() != 1 && request.getVoteType() != -1) {
            throw new RuntimeException("Vote type must be 1 (upvote) or -1 (downvote)");
        }

        Vote vote;

        if (request.getPostId() != null) {
            vote = voteOnPost(request.getPostId(), request.getVoteType(), currentUser);
        } else {
            vote = voteOnComment(request.getCommentId(), request.getVoteType(), currentUser);
        }

        return convertToResponse(vote);
    }

    @Transactional
    public void removeVote(Long postId, Long commentId, User currentUser) {
        if ((postId == null && commentId == null) || (postId != null && commentId != null)) {
            throw new RuntimeException("Must specify either postId or commentId, not both");
        }

        if (postId != null) {
            voteRepository.deleteByUserIdAndPostId(currentUser.getId(), postId);
        } else {
            voteRepository.deleteByUserIdAndCommentId(currentUser.getId(), commentId);
        }
    }

    public VoteScoreResponse getPostVoteScore(Long postId, User currentUser) {
        Integer score = voteRepository.getPostVoteScore(postId);

        Short userVote = null;
        if (currentUser != null) {
            Optional<Vote> vote = voteRepository.findByUserIdAndPostId(currentUser.getId(), postId);
            if (vote.isPresent()) {
                userVote = vote.get().getVoteType();
            }
        }

        return new VoteScoreResponse(score, userVote);
    }

    public VoteScoreResponse getCommentVoteScore(Long commentId, User currentUser) {
        Integer score = voteRepository.getCommentVoteScore(commentId);

        Short userVote = null;
        if (currentUser != null) {
            Optional<Vote> vote = voteRepository.findByUserIdAndCommentId(currentUser.getId(), commentId);
            if (vote.isPresent()) {
                userVote = vote.get().getVoteType();
            }
        }

        return new VoteScoreResponse(score, userVote);
    }

    private Vote voteOnPost(Long postId, Short voteType, User currentUser) {
        Post post = postRepository.findById(postId)
                .orElseThrow(() -> new RuntimeException("Post not found"));

        if (post.getIsDeleted()) {
            throw new RuntimeException("Cannot vote on a deleted post");
        }

        Optional<Vote> existingVote = voteRepository.findByUserIdAndPostId(currentUser.getId(), postId);

        if (existingVote.isPresent()) {
            Vote vote = existingVote.get();

            if (vote.getVoteType().equals(voteType)) {
                // Same vote - remove it (toggle off)
                voteRepository.delete(vote);
                return vote;
            } else {
                // Different vote - update it
                vote.setVoteType(voteType);
                return voteRepository.save(vote);
            }
        } else {
            // New vote
            Vote vote = Vote.builder()
                    .user(currentUser)
                    .post(post)
                    .voteType(voteType)
                    .build();
            return voteRepository.save(vote);
        }
    }

    private Vote voteOnComment(Long commentId, Short voteType, User currentUser) {
        Comment comment = commentRepository.findById(commentId)
                .orElseThrow(() -> new RuntimeException("Comment not found"));

        if (comment.getIsDeleted()) {
            throw new RuntimeException("Cannot vote on a deleted comment");
        }

        Optional<Vote> existingVote = voteRepository.findByUserIdAndCommentId(currentUser.getId(), commentId);

        if (existingVote.isPresent()) {
            Vote vote = existingVote.get();

            if (vote.getVoteType().equals(voteType)) {
                // Same vote - remove it (toggle off)
                voteRepository.delete(vote);
                return vote;
            } else {
                // Different vote - update it
                vote.setVoteType(voteType);
                return voteRepository.save(vote);
            }
        } else {
            // New vote
            Vote vote = Vote.builder()
                    .user(currentUser)
                    .comment(comment)
                    .voteType(voteType)
                    .build();
            return voteRepository.save(vote);
        }
    }

    private VoteResponse convertToResponse(Vote vote) {
        return VoteResponse.builder()
                .id(vote.getId())
                .userId(vote.getUser().getId())
                .postId(vote.getPost() != null ? vote.getPost().getId() : null)
                .commentId(vote.getComment() != null ? vote.getComment().getId() : null)
                .voteType(vote.getVoteType())
                .createdAt(vote.getCreatedAt())
                .build();
    }
}