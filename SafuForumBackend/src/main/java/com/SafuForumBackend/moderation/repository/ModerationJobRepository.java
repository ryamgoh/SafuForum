package com.SafuForumBackend.moderation.repository;

import com.SafuForumBackend.moderation.entity.ModerationJob;
import com.SafuForumBackend.moderation.enums.ModerationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ModerationJobRepository extends JpaRepository<ModerationJob, Long> {

    List<ModerationJob> findByPostIdAndPostVersion(Long postId, Integer postVersion);

    List<ModerationJob> findByStatusAndCreatedAtBefore(ModerationStatus status, LocalDateTime cutoff);

    @Modifying
    @Query("""
            UPDATE ModerationJob mj
            SET mj.status = :toStatus,
                mj.errorMessage = :errorMessage,
                mj.updatedAt = :updatedAt
            WHERE mj.post.id = :postId
              AND mj.postVersion = :postVersion
              AND mj.status = :fromStatus
            """)
    int updateStatusForPostVersion(
            @Param("postId") Long postId,
            @Param("postVersion") Integer postVersion,
            @Param("fromStatus") ModerationStatus fromStatus,
            @Param("toStatus") ModerationStatus toStatus,
            @Param("errorMessage") String errorMessage,
            @Param("updatedAt") LocalDateTime updatedAt
    );
}

