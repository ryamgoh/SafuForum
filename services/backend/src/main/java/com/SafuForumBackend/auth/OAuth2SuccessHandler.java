package com.SafuForumBackend.auth;

import com.SafuForumBackend.auth.dto.AuthResponse;
import com.SafuForumBackend.auth.service.AuthService;
import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.user.repository.UserRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;

@Component
@RequiredArgsConstructor
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final UserRepository userRepository;
    private final AuthService authService;

    @Override
    public void onAuthenticationSuccess(
            HttpServletRequest request,
            HttpServletResponse response,
            Authentication authentication) throws IOException {

        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();

        String email = oAuth2User.getAttribute("email");
        String name = oAuth2User.getAttribute("name");
        String picture = oAuth2User.getAttribute("picture");
        String googleId = oAuth2User.getAttribute("sub");

        User user = userRepository
                .findByOauthProviderAndOauthProviderId("google", googleId)
                .orElseGet(() -> {
                    User newUser = User.builder()
                            .email(email)
                            .username(generateUsername(email))
                            .displayName(name)
                            .avatarUrl(picture)
                            .oauthProvider("google")
                            .oauthProviderId(googleId)
                            .build();
                    return userRepository.save(newUser);
                });

        user.setLastLoginAt(LocalDateTime.now());
        userRepository.save(user);

        AuthResponse authResponse = authService.createAuthTokens(user);

        String redirectUrl = String.format(
                "http://localhost:3000/auth/callback?accessToken=%s&refreshToken=%s",
                URLEncoder.encode(authResponse.getAccessToken(), StandardCharsets.UTF_8),
                URLEncoder.encode(authResponse.getRefreshToken(), StandardCharsets.UTF_8)
        );

        getRedirectStrategy().sendRedirect(request, response, redirectUrl);
    }

    private String generateUsername(String email) {
        String base = email.split("@")[0];
        String username = base;
        int counter = 1;

        while (userRepository.existsByUsername(username)) {
            username = base + counter++;
        }
        return username;
    }
}