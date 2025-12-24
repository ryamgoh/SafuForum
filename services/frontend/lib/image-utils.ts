/**
 * Utility functions for image handling
 */

// Construct full image URL from backend response
export function getImageUrl(relativeUrl: string): string {
  // Backend returns: "bucket-name/uploads/uuid.jpg"
  // We need: "http://localhost:8333/bucket-name/uploads/uuid.jpg"

  // In production, this would use your CDN/domain
  const baseUrl = process.env.NEXT_PUBLIC_SEAWEEDFS_URL || 'http://localhost:8333';

  // Remove leading slash if present
  const cleanUrl = relativeUrl.startsWith('/') ? relativeUrl.slice(1) : relativeUrl;

  return `${baseUrl}/${cleanUrl}`;
}

// Validate image file type
export function isValidImageType(file: File): boolean {
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  return validTypes.includes(file.type);
}

// Validate image file size (10MB max)
export function isValidImageSize(file: File): boolean {
  const maxSize = 10 * 1024 * 1024; // 10MB in bytes
  return file.size <= maxSize;
}

// Format file size for display
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Get image file extension
export function getFileExtension(filename: string): string {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2);
}

// Validate image before upload
export interface ImageValidationResult {
  valid: boolean;
  error?: string;
}

export function validateImage(file: File): ImageValidationResult {
  if (!isValidImageType(file)) {
    return {
      valid: false,
      error: 'Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed.'
    };
  }

  if (!isValidImageSize(file)) {
    return {
      valid: false,
      error: 'File size exceeds 10MB limit.'
    };
  }

  return { valid: true };
}

