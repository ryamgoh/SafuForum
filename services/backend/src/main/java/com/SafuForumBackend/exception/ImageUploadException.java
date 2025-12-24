package com.SafuForumBackend.exception;

/**
 * Custom exception for image upload related errors
 * Provides more specific error handling for image operations
 */
public class ImageUploadException extends RuntimeException {

    public ImageUploadException(String message) {
        super(message);
    }

    public ImageUploadException(String message, Throwable cause) {
        super(message, cause);
    }
}

