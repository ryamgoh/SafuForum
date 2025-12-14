package com.SafuForumBackend.auth.service;

import com.SafuForumBackend.auth.entity.RefreshToken;
import com.SafuForumBackend.auth.repository.RefreshTokenRepository;
import com.SafuForumBackend.auth.dto.AuthResponse;
import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final JwtService jwtService;

    @Transactional
    public AuthResponse createAuthTokens(User user) {
        String accessToken = jwtService.generateAccessToken(user.getId(), user.getRole());

        String refreshTokenValue = jwtService.generateRefreshToken(user.getId());

        RefreshToken refreshToken = RefreshToken.builder()
                .user(user)
                .token(refreshTokenValue)
                .expiresAt(jwtService.getRefreshTokenExpiration())
                .build();

        refreshTokenRepository.save(refreshToken);

        return AuthResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshTokenValue)
                .tokenType("Bearer")
                .expiresIn(900) // 15 minutes in seconds
                .userId(user.getId())
                .username(user.getUsername())
                .role(user.getRole().name())
                .build();
    }

    @Transactional
    public AuthResponse refreshAccessToken(String refreshTokenValue) {
        if (!jwtService.isTokenValid(refreshTokenValue) ||
                !jwtService.isRefreshToken(refreshTokenValue)) {
            throw new RuntimeException("Invalid refresh token");
        }

        RefreshToken refreshToken = refreshTokenRepository
                .findByToken(refreshTokenValue)
                .orElseThrow(() -> new RuntimeException("Refresh token not found"));

        if (!refreshToken.isValid()) {
            throw new RuntimeException("Refresh token expired or revoked");
        }

        User user = refreshToken.getUser();
        String newAccessToken = jwtService.generateAccessToken(user.getId(), user.getRole());

        return AuthResponse.builder()
                .accessToken(newAccessToken)
                .refreshToken(refreshTokenValue) // Return same refresh token
                .tokenType("Bearer")
                .expiresIn(900)
                .userId(user.getId())
                .username(user.getUsername())
                .role(user.getRole().name())
                .build();
    }

    @Transactional
    public void revokeRefreshToken(String token) {
        refreshTokenRepository.findByToken(token)
                .ifPresent(refreshToken -> {
                    refreshToken.setRevoked(true);
                    refreshTokenRepository.save(refreshToken);
                });
    }

    @Transactional
    public void revokeAllUserTokens(Long userId) {
        refreshTokenRepository.deleteByUser_Id(userId);
    }
}