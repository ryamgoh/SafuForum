package com.SafuForumBackend.post.repository;

import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.tag.entity.Tag;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.time.LocalDateTime;

@Repository
public interface PostRepository extends JpaRepository<Post, Long> {

    // Fixed method names
    Page<Post> findByIsDeletedFalse(Pageable pageable);

    Page<Post> findByAuthorIdAndIsDeletedFalse(Long authorId, Pageable pageable);

    Page<Post> findByTagsContainingAndIsDeletedFalse(Tag tag, Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.isDeleted = false AND p.createdAt > :since ORDER BY (SELECT COALESCE(SUM(v.voteType), 0) FROM Vote v WHERE v.post = p) DESC")
    Page<Post> findTrendingPosts(@Param("since") LocalDateTime since, Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.isDeleted = false ORDER BY (SELECT COUNT(c) FROM Comment c WHERE c.post = p AND c.isDeleted = false) DESC")
    Page<Post> findMostDiscussed(Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.isDeleted = false ORDER BY ((SELECT COALESCE(SUM(v.voteType), 0) FROM Vote v WHERE v.post = p) + (SELECT COUNT(c) FROM Comment c WHERE c.post = p AND c.isDeleted = false) * 0.5) DESC")
    Page<Post> findHotPosts(Pageable pageable);
}