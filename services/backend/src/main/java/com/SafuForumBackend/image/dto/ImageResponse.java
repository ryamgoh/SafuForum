package com.SafuForumBackend.image.dto;

public record ImageResponse(
        Long id,
        String url,
        String originalFilename,
        Long fileSize,
        String mimeType,
        Integer displayOrder
) {}
