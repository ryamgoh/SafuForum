package com.SafuForumBackend.comment.repository;

import com.SafuForumBackend.comment.entity.Comment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Long> {

    List<Comment> findByPostIdAndParentCommentIsNullAndIsDeletedFalseOrderByCreatedAtAsc(Long postId);

    List<Comment> findByParentCommentIdAndIsDeletedFalseOrderByCreatedAtAsc(Long parentCommentId);

    long countByPostIdAndIsDeletedFalse(Long postId);

    List<Comment> findByAuthorIdAndIsDeletedFalseOrderByCreatedAtDesc(Long authorId);
}