package com.SafuForumBackend.user.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import com.SafuForumBackend.user.entity.User;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
    Optional<User> findByEmail(String email);
    Optional<User> findByOauthProviderAndOauthProviderId(String provider, String providerId);
    boolean existsByUsername(String username);
    boolean existsByEmail(String email);
}