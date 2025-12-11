package com.SafuForumBackend.vote.controller;

import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.vote.dto.VoteRequest;
import com.SafuForumBackend.vote.dto.VoteResponse;
import com.SafuForumBackend.vote.dto.VoteScoreResponse;
import com.SafuForumBackend.vote.service.VoteService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/votes")
@RequiredArgsConstructor
public class VoteController {

    private final VoteService voteService;

    @PostMapping
    public ResponseEntity<VoteResponse> vote(
            @Valid @RequestBody VoteRequest request,
            @AuthenticationPrincipal User currentUser) {

        if (currentUser == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        VoteResponse vote = voteService.vote(request, currentUser);
        return ResponseEntity.ok(vote);
    }

    @DeleteMapping
    public ResponseEntity<Void> removeVote(
            @RequestParam(required = false) Long postId,
            @RequestParam(required = false) Long commentId,
            @AuthenticationPrincipal User currentUser) {

        if (currentUser == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        voteService.removeVote(postId, commentId, currentUser);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/post/{postId}")
    public ResponseEntity<VoteScoreResponse> getPostVoteScore(
            @PathVariable Long postId,
            @AuthenticationPrincipal User currentUser) {

        VoteScoreResponse score = voteService.getPostVoteScore(postId, currentUser);
        return ResponseEntity.ok(score);
    }

    @GetMapping("/comment/{commentId}")
    public ResponseEntity<VoteScoreResponse> getCommentVoteScore(
            @PathVariable Long commentId,
            @AuthenticationPrincipal User currentUser) {

        VoteScoreResponse score = voteService.getCommentVoteScore(commentId, currentUser);
        return ResponseEntity.ok(score);
    }
}