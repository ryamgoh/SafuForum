package com.SafuForumBackend.user.service;

import com.SafuForumBackend.user.repository.UserRepository;
import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.user.dto.UserResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;

    public UserResponse getUserById(Long id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found"));

        return UserResponse.builder()
                .id(user.getId())
                .username(user.getUsername())
                .displayName(user.getDisplayName())
                .avatarUrl(user.getAvatarUrl())
                .bio(user.getBio())
                .role(user.getRole().toString())
                .reputation(user.getReputation())
                .createdAt(user.getCreatedAt().toString())
                .build();
    }
}