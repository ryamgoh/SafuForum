package com.SafuForumBackend.image.repository;

import com.SafuForumBackend.image.entity.Image;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ImageRepository extends JpaRepository<Image, Long> {

    // Find all images for a post, ordered by display order
    List<Image> findByPostIdOrderByDisplayOrderAsc(Long postId);

    // Find all images for a comment, ordered by display order
    List<Image> findByCommentIdOrderByDisplayOrderAsc(Long commentId);

    // Find all images uploaded by a user
    List<Image> findByUploaderIdOrderByCreatedAtDesc(Long uploaderId);

    // Find orphaned images (not attached to any post or comment) older than a certain time
    @Query("SELECT i FROM Image i WHERE i.post IS NULL AND i.comment IS NULL " +
            "AND i.createdAt < :cutoffTime AND i.deletedAt IS NULL")
    List<Image> findOrphanedImagesOlderThan(@Param("cutoffTime") LocalDateTime cutoffTime);

    // Find all non-deleted images for a post
    @Query("SELECT i FROM Image i WHERE i.post.id = :postId AND i.deletedAt IS NULL " +
            "ORDER BY i.displayOrder ASC")
    List<Image> findActiveImagesByPostId(@Param("postId") Long postId);

    // Find all non-deleted images for a comment
    @Query("SELECT i FROM Image i WHERE i.comment.id = :commentId AND i.deletedAt IS NULL " +
            "ORDER BY i.displayOrder ASC")
    List<Image> findActiveImagesByCommentId(@Param("commentId") Long commentId);

    // Count active images for a post (for validation - max 10 images)
    @Query("SELECT COUNT(i) FROM Image i WHERE i.post.id = :postId AND i.deletedAt IS NULL")
    long countActiveImagesByPostId(@Param("postId") Long postId);

    // Count active images for a comment (for validation - max 3 images)
    @Query("SELECT COUNT(i) FROM Image i WHERE i.comment.id = :commentId AND i.deletedAt IS NULL")
    long countActiveImagesByCommentId(@Param("commentId") Long commentId);

    // Find image by SeaweedFS FID
    Image findBySeaweedfsFid(String seaweedfsFid);
}