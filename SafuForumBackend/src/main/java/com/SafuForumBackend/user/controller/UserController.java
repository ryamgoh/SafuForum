package com.SafuForumBackend.user.controller;

import com.SafuForumBackend.user.dto.UserResponse;
import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.user.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        UserResponse user = userService.getUserById(id);
        return ResponseEntity.ok(user);
    }

    @GetMapping("/me")
    public ResponseEntity<UserResponse> getCurrentUser(@AuthenticationPrincipal User user) {
        if (user == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        return ResponseEntity.ok(UserResponse.builder()
                .id(user.getId())
                .username(user.getUsername())
                .displayName(user.getDisplayName())
                .avatarUrl(user.getAvatarUrl())
                .bio(user.getBio())
                .role(user.getRole().toString())  // ADD THIS
                .reputation(user.getReputation())
                .createdAt(user.getCreatedAt().toString())  // ADD THIS
                .build());
    }
}