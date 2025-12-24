package com.SafuForumBackend.vote.repository;

import com.SafuForumBackend.vote.entity.Vote;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface VoteRepository extends JpaRepository<Vote, Long> {

    Optional<Vote> findByUserIdAndPostId(Long userId, Long postId);

    Optional<Vote> findByUserIdAndCommentId(Long userId, Long commentId);

    @Query("SELECT COALESCE(SUM(v.voteType), 0) FROM Vote v WHERE v.post.id = :postId")
    Integer getPostVoteScore(@Param("postId") Long postId);

    @Query("SELECT COALESCE(SUM(v.voteType), 0) FROM Vote v WHERE v.comment.id = :commentId")
    Integer getCommentVoteScore(@Param("commentId") Long commentId);

    void deleteByUserIdAndPostId(Long userId, Long postId);

    void deleteByUserIdAndCommentId(Long userId, Long commentId);
}