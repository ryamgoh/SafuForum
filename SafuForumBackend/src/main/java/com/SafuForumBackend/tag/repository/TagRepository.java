package com.SafuForumBackend.tag.repository;

import com.SafuForumBackend.tag.entity.Tag;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface TagRepository extends JpaRepository<Tag, Long> {

    Optional<Tag> findBySlug(String slug);

    Optional<Tag> findByName(String name);

    boolean existsBySlug(String slug);

    @Query(value = "SELECT COUNT(pt.post_id) FROM post_tags pt " +
            "JOIN posts p ON pt.post_id = p.id " +
            "WHERE pt.tag_id = :tagId AND p.is_deleted = false",
            nativeQuery = true)
    Long countPostsByTagId(@Param("tagId") Long tagId);
}