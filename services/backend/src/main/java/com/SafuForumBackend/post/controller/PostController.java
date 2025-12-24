package com.SafuForumBackend.post.controller;

import com.SafuForumBackend.post.dto.CreatePostRequest;
import com.SafuForumBackend.post.dto.PostResponse;
import com.SafuForumBackend.post.dto.UpdatePostRequest;
import com.SafuForumBackend.post.service.PostService;
import com.SafuForumBackend.user.entity.User;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/posts")
@RequiredArgsConstructor
public class PostController {

    private final PostService postService;

    @PostMapping
    public ResponseEntity<PostResponse> createPost(
            @Valid @RequestBody CreatePostRequest request,
            @AuthenticationPrincipal User currentUser) {

        if (currentUser == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        PostResponse post = postService.createPost(request, currentUser);
        return ResponseEntity.status(HttpStatus.CREATED).body(post);
    }

    @GetMapping
    public ResponseEntity<Page<PostResponse>> getAllPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Page<PostResponse> posts = postService.getAllPosts(page, size);
        return ResponseEntity.ok(posts);
    }

    @GetMapping("/{id}")
    public ResponseEntity<PostResponse> getPost(@PathVariable Long id) {
        PostResponse post = postService.getPostById(id);
        return ResponseEntity.ok(post);
    }

    @GetMapping("/trending")
    public ResponseEntity<Page<PostResponse>> getTrendingPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "7") int days) {

        Page<PostResponse> posts = postService.getTrendingPosts(page, size, days);
        return ResponseEntity.ok(posts);
    }

    @GetMapping("/discussed")
    public ResponseEntity<Page<PostResponse>> getMostDiscussedPosts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Page<PostResponse> posts = postService.getMostDiscussedPosts(page, size);
        return ResponseEntity.ok(posts);
    }

    @GetMapping("/tag/{tagSlug}")
    public ResponseEntity<Page<PostResponse>> getPostsByTag(
            @PathVariable String tagSlug,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Page<PostResponse> posts = postService.getPostsByTag(tagSlug, page, size);
        return ResponseEntity.ok(posts);
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<Page<PostResponse>> getPostsByUser(
            @PathVariable Long userId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        Page<PostResponse> posts = postService.getPostsByUser(userId, page, size);
        return ResponseEntity.ok(posts);
    }

    @PutMapping("/{id}")
    public ResponseEntity<PostResponse> updatePost(
            @PathVariable Long id,
            @Valid @RequestBody UpdatePostRequest request,
            @AuthenticationPrincipal User currentUser) {

        if (currentUser == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        PostResponse post = postService.updatePost(id, request, currentUser);
        return ResponseEntity.ok(post);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deletePost(
            @PathVariable Long id,
            @AuthenticationPrincipal User currentUser) {

        if (currentUser == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        postService.deletePost(id, currentUser);
        return ResponseEntity.noContent().build();
    }
}