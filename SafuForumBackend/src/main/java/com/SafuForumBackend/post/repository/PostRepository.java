package com.SafuForumBackend.post.repository;

import com.SafuForumBackend.post.entity.Post;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface PostRepository extends JpaRepository<Post, Long> {

    Page<Post> findByIsDeletedFalseOrderByCreatedAtDesc(Pageable pageable);

    Page<Post> findByAuthorIdAndIsDeletedFalseOrderByCreatedAtDesc(Long authorId, Pageable pageable);

    @Query("SELECT p FROM Post p JOIN p.tags t WHERE t.slug = :tagSlug AND p.isDeleted = false ORDER BY p.createdAt DESC")
    Page<Post> findByTagSlug(@Param("tagSlug") String tagSlug, Pageable pageable);
}