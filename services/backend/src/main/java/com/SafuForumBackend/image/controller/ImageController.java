package com.SafuForumBackend.image.controller;

import com.SafuForumBackend.image.entity.Image;
import com.SafuForumBackend.image.service.ImageService;
import com.SafuForumBackend.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/images")
@RequiredArgsConstructor
public class ImageController {

    private final ImageService imageService;

    /**
     * Upload a single image
     * POST /api/images/upload
     */
    @PostMapping("/upload")
    public ResponseEntity<?> uploadImage(
            @RequestParam("file") MultipartFile file,
            @AuthenticationPrincipal User currentUser
    ) {
        try {
            Image uploadedImage = imageService.uploadImage(file, currentUser);

            Map<String, Object> response = new HashMap<>();
            response.put("id", uploadedImage.getId());
            response.put("url", uploadedImage.getSeaweedfsUrl());
            response.put("originalFilename", uploadedImage.getOriginalFilename());
            response.put("fileSize", uploadedImage.getFileSizeBytes());
            response.put("mimeType", uploadedImage.getMimeType());
            response.put("createdAt", uploadedImage.getCreatedAt());

            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));

        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Failed to upload image: " + e.getMessage()));
        }
    }

    /**
     * Get image metadata by ID
     * GET /api/images/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getImage(@PathVariable Long id) {
        return imageService.getImageById(id)
                .map(image -> {
                    Map<String, Object> response = new HashMap<>();
                    response.put("id", image.getId());
                    response.put("url", image.getSeaweedfsUrl());
                    response.put("originalFilename", image.getOriginalFilename());
                    response.put("fileSize", image.getFileSizeBytes());
                    response.put("mimeType", image.getMimeType());
                    response.put("uploadStatus", image.getUploadStatus());
                    response.put("createdAt", image.getCreatedAt());
                    response.put("isDeleted", image.isDeleted());

                    return ResponseEntity.ok(response);
                })
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Get images for a specific post
     * GET /api/images/post/{postId}
     */
    @GetMapping("/post/{postId}")
    public ResponseEntity<List<ImageDTO>> getImagesForPost(@PathVariable Long postId) {
        List<Image> images = imageService.getImagesForPost(postId);
        List<ImageDTO> imageDTOs = images.stream()
                .map(this::convertToDTO)
                .toList();
        return ResponseEntity.ok(imageDTOs);
    }

    /**
     * Get images for a specific comment
     * GET /api/images/comment/{commentId}
     */
    @GetMapping("/comment/{commentId}")
    public ResponseEntity<List<ImageDTO>> getImagesForComment(@PathVariable Long commentId) {
        List<Image> images = imageService.getImagesForComment(commentId);
        List<ImageDTO> imageDTOs = images.stream()
                .map(this::convertToDTO)
                .toList();
        return ResponseEntity.ok(imageDTOs);
    }

    /**
     * Delete an image (soft delete)
     * DELETE /api/images/{id}
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteImage(
            @PathVariable Long id,
            @AuthenticationPrincipal User currentUser
    ) {
        try {
            // TODO: Add authorization check - only uploader or moderators can delete
            imageService.softDeleteImage(id);
            return ResponseEntity.ok(Map.of("message", "Image deleted successfully"));

        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    // Helper method to convert Image entity to DTO
    private ImageDTO convertToDTO(Image image) {
        return new ImageDTO(
                image.getId(),
                image.getSeaweedfsUrl(),
                image.getOriginalFilename(),
                image.getFileSizeBytes(),
                image.getMimeType(),
                image.getDisplayOrder()
        );
    }

    // Simple DTO for image responses
    record ImageDTO(
            Long id,
            String url,
            String originalFilename,
            Long fileSize,
            String mimeType,
            Integer displayOrder
    ) {}
}