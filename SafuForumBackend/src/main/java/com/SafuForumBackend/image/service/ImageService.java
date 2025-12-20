package com.SafuForumBackend.image.service;

import com.SafuForumBackend.config.S3Config;
import com.SafuForumBackend.image.entity.Image;
import com.SafuForumBackend.image.repository.ImageRepository;
import com.SafuForumBackend.user.entity.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CreateBucketRequest;
import software.amazon.awssdk.services.s3.model.DeleteObjectRequest;
import software.amazon.awssdk.services.s3.model.HeadBucketRequest;
import software.amazon.awssdk.services.s3.model.NoSuchBucketException;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;

@Slf4j
@Service
@RequiredArgsConstructor
public class ImageService {

    private final ImageRepository imageRepository;
    private final S3Client s3Client;
    private final S3Config s3Config;

    private final AtomicBoolean bucketInitialized = new AtomicBoolean(false);

    // Allowed image formats
    private static final List<String> ALLOWED_MIME_TYPES = Arrays.asList(
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp"
    );

    // Max file size: 10MB
    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024;

    /**
     * Ensure S3 bucket exists (lazy initialization on first upload)
     */
    private void ensureBucketExists() {
        if (bucketInitialized.get()) {
            return;
        }

        synchronized (this) {
            if (bucketInitialized.get()) {
                return;
            }

            String bucketName = s3Config.getBucketName();
            int maxRetries = 3;
            int retryDelayMs = 1000;

            for (int i = 0; i < maxRetries; i++) {
                try {
                    s3Client.headBucket(HeadBucketRequest.builder()
                            .bucket(bucketName)
                            .build());
                    log.info("S3 bucket '{}' already exists", bucketName);
                    bucketInitialized.set(true);
                    return;
                } catch (NoSuchBucketException e) {
                    try {
                        s3Client.createBucket(CreateBucketRequest.builder()
                                .bucket(bucketName)
                                .build());
                        log.info("S3 bucket '{}' created successfully", bucketName);
                        bucketInitialized.set(true);
                        return;
                    } catch (Exception createEx) {
                        log.warn("Attempt {} to create bucket failed: {}", i + 1, createEx.getMessage());
                    }
                } catch (Exception e) {
                    log.warn("Attempt {} to check bucket failed: {}", i + 1, e.getMessage());
                }

                if (i < maxRetries - 1) {
                    try {
                        Thread.sleep(retryDelayMs);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("Interrupted while initializing S3 bucket", ie);
                    }
                }
            }

            throw new RuntimeException("Failed to initialize S3 bucket '" + bucketName + "' after " + maxRetries + " attempts");
        }
    }

    /**
     * Upload image to SeaweedFS and create database record
     */
    @Transactional
    public Image uploadImage(MultipartFile file, User uploader) throws IOException {
        // Ensure bucket exists before upload
        ensureBucketExists();

        // Validate file
        validateImageFile(file);

        // Generate unique filename
        String originalFilename = file.getOriginalFilename();
        String extension = getFileExtension(originalFilename);
        String uniqueFilename = UUID.randomUUID().toString() + extension;
        String s3Key = "uploads/" + uniqueFilename;

        // Upload to SeaweedFS via S3 API
        PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                .bucket(s3Config.getBucketName())
                .key(s3Key)
                .contentType(file.getContentType())
                .contentLength(file.getSize())
                .build();

        s3Client.putObject(putObjectRequest, RequestBody.fromBytes(file.getBytes()));

        String imageUrl = constructImageUrl(s3Key);

        Image image = Image.builder()
                .uploader(uploader)
                .seaweedfsFid(s3Key) // Use S3 key as FID
                .seaweedfsUrl(imageUrl)
                .originalFilename(originalFilename)
                .fileSizeBytes(file.getSize())
                .mimeType(file.getContentType())
                .uploadStatus("COMPLETED")
                .displayOrder(0) // Will be set when attached to post/comment
                .build();

        return imageRepository.save(image);
    }

    /**
     * Soft delete image (mark as deleted in DB, but don't remove from SeaweedFS yet)
     */
    @Transactional
    public void softDeleteImage(Long imageId) {
        Image image = imageRepository.findById(imageId)
                .orElseThrow(() -> new IllegalArgumentException("Image not found: " + imageId));

        image.markAsDeleted();
        imageRepository.save(image);
    }

    /**
     * Hard delete image (remove from both DB and SeaweedFS)
     */
    @Transactional
    public void hardDeleteImage(Long imageId) {
        Image image = imageRepository.findById(imageId)
                .orElseThrow(() -> new IllegalArgumentException("Image not found: " + imageId));

        // Delete from SeaweedFS
        deleteFromS3(image.getSeaweedfsFid());

        // Delete from database
        imageRepository.delete(image);
    }

    public java.util.Optional<Image> getImageById(Long imageId) {
        return imageRepository.findById(imageId);
    }

    /**
     * Get images for a post
     */
    public List<Image> getImagesForPost(Long postId) {
        return imageRepository.findActiveImagesByPostId(postId);
    }

    /**
     * Get images for a comment
     */
    public List<Image> getImagesForComment(Long commentId) {
        return imageRepository.findActiveImagesByCommentId(commentId);
    }

    /**
     * Validate that a post hasn't exceeded the image limit (10 images)
     */
    public void validatePostImageLimit(Long postId) {
        long count = imageRepository.countActiveImagesByPostId(postId);
        if (count >= 10) {
            throw new IllegalArgumentException("Post already has maximum number of images (10)");
        }
    }

    /**
     * Validate that a comment hasn't exceeded the image limit (3 images)
     */
    public void validateCommentImageLimit(Long commentId) {
        long count = imageRepository.countActiveImagesByCommentId(commentId);
        if (count >= 3) {
            throw new IllegalArgumentException("Comment already has maximum number of images (3)");
        }
    }

    /**
     * Scheduled job: Clean up orphaned images (uploaded but never attached to post/comment)
     * Runs daily at 3 AM
     */
    @Scheduled(cron = "0 0 3 * * *")
    @Transactional
    public void cleanupOrphanedImages() {
        LocalDateTime cutoffTime = LocalDateTime.now().minusHours(24);
        List<Image> orphanedImages = imageRepository.findOrphanedImagesOlderThan(cutoffTime);

        int deletedCount = 0;
        for (Image image : orphanedImages) {
            try {
                // Delete from SeaweedFS
                deleteFromS3(image.getSeaweedfsFid());
                // Delete from database
                imageRepository.delete(image);
                deletedCount++;
            } catch (Exception e) {
                log.error("Failed to delete orphaned image {}: {}", image.getId(), e.getMessage());
            }
        }

        if (deletedCount > 0) {
            log.info("Cleaned up {} orphaned images", deletedCount);
        }
    }


    private void validateImageFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("File cannot be empty");
        }

        if (file.getSize() > MAX_FILE_SIZE) {
            throw new IllegalArgumentException("File size exceeds maximum limit of 10MB");
        }

        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_MIME_TYPES.contains(contentType.toLowerCase())) {
            throw new IllegalArgumentException("Invalid file type. Allowed types: JPEG, PNG, GIF, WebP");
        }

        String filename = file.getOriginalFilename();
        if (filename == null || !hasValidImageExtension(filename)) {
            throw new IllegalArgumentException("Invalid file extension");
        }
    }

    private boolean hasValidImageExtension(String filename) {
        String lower = filename.toLowerCase();
        return lower.endsWith(".jpg") ||
                lower.endsWith(".jpeg") ||
                lower.endsWith(".png") ||
                lower.endsWith(".gif") ||
                lower.endsWith(".webp");
    }

    private String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf("."));
    }

    private String constructImageUrl(String s3Key) {
        // Construct public URL to access the image
        // Format: http://seaweed-s3:8333/bucket-name/uploads/uuid.jpg
        return s3Config.getBucketName() + "/" + s3Key;
    }

    private void deleteFromS3(String s3Key) {
        try {
            DeleteObjectRequest deleteRequest = DeleteObjectRequest.builder()
                    .bucket(s3Config.getBucketName())
                    .key(s3Key)
                    .build();
            s3Client.deleteObject(deleteRequest);
        } catch (Exception e) {
            log.error("Failed to delete from S3: {} - {}", s3Key, e.getMessage());
            // Don't throw - continue with DB deletion even if S3 deletion fails
        }
    }
}