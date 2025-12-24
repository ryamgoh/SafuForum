package com.SafuForumBackend.image.entity;

import com.SafuForumBackend.comment.entity.Comment;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.user.entity.User;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "images")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Image {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "uploader_id", nullable = false)
    private User uploader;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "post_id")
    private Post post;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "comment_id")
    private Comment comment;

    @Column(name = "display_order", nullable = false)
    private Integer displayOrder;

    @Column(name = "seaweedfs_fid", nullable = false)
    private String seaweedfsFid;

    @Column(name = "seaweedfs_url", nullable = false, length = 500)
    private String seaweedfsUrl;

    @Column(name = "original_filename", nullable = false)
    private String originalFilename;

    @Column(name = "file_size_bytes", nullable = false)
    private Long fileSizeBytes;

    @Column(name = "mime_type", nullable = false, length = 50)
    private String mimeType;

    @Column(name = "upload_status", nullable = false, length = 20)
    @Builder.Default
    private String uploadStatus = "COMPLETED";

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }

    public boolean isDeleted() {
        return deletedAt != null;
    }

    public void markAsDeleted() {
        this.deletedAt = LocalDateTime.now();
        this.uploadStatus = "DELETED";
    }

    public boolean belongsToPost() {
        return post != null && comment == null;
    }

    public boolean belongsToComment() {
        return comment != null && post == null;
    }
}