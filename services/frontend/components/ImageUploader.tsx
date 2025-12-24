'use client';

import { useState, useRef, DragEvent } from 'react';
import { Upload, X, Image as ImageIcon, Loader2 } from 'lucide-react';
import { imagesApi } from '@/lib/api';
import { ImageResponse } from '@/lib/types';
import { validateImage, formatFileSize, getImageUrl } from '@/lib/image-utils';
import toast from 'react-hot-toast';
import Image from 'next/image';

interface ImageUploaderProps {
  maxImages: number; // 10 for posts, 3 for comments
  onImagesChange: (imageIds: number[]) => void;
  initialImages?: ImageResponse[];
  disabled?: boolean;
}

interface UploadedImage extends ImageResponse {
  previewUrl: string;
}

export default function ImageUploader({
  maxImages,
  onImagesChange,
  initialImages = [],
  disabled = false
}: ImageUploaderProps) {
  const [images, setImages] = useState<UploadedImage[]>(
    initialImages.map(img => ({
      ...img,
      previewUrl: getImageUrl(img.url)
    }))
  );
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const remainingSlots = maxImages - images.length;
    if (remainingSlots <= 0) {
      toast.error(`Maximum ${maxImages} images allowed`);
      return;
    }

    const filesToUpload = Array.from(files).slice(0, remainingSlots);
    const validFiles: File[] = [];

    // Validate all files first
    for (const file of filesToUpload) {
      const validation = validateImage(file);
      if (!validation.valid) {
        toast.error(`${file.name}: ${validation.error}`);
      } else {
        validFiles.push(file);
      }
    }

    if (validFiles.length === 0) return;

    setUploading(true);

    // Upload files sequentially
    const newImages: UploadedImage[] = [];
    for (const file of validFiles) {
      try {
        const response = await imagesApi.upload(file);
        const uploadedImage = response.data;

        newImages.push({
          id: uploadedImage.id,
          url: uploadedImage.url,
          originalFilename: uploadedImage.originalFilename,
          fileSize: uploadedImage.fileSize,
          mimeType: uploadedImage.mimeType,
          displayOrder: images.length + newImages.length + 1,
          previewUrl: getImageUrl(uploadedImage.url)
        });

        toast.success(`${file.name} uploaded successfully`);
      } catch (error: any) {
        console.error('Upload error:', error);

        // Extract backend error message with better handling
        let errorMessage = 'Upload failed';

        if (error.response?.data) {
          // Handle JSON error responses
          if (typeof error.response.data === 'object') {
            errorMessage = error.response.data.message ||
                          error.response.data.error ||
                          errorMessage;
          }
          // Handle string error responses
          else if (typeof error.response.data === 'string') {
            errorMessage = error.response.data;
          }
        }
        // Fallback to error message
        else if (error.message) {
          errorMessage = error.message;
        }

        toast.error(`${file.name}: ${errorMessage}`);
      }
    }

    const updatedImages = [...images, ...newImages];
    setImages(updatedImages);
    onImagesChange(updatedImages.map(img => img.id));
    setUploading(false);

    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveImage = async (imageId: number) => {
    try {
      await imagesApi.delete(imageId);
      const updatedImages = images.filter(img => img.id !== imageId);
      setImages(updatedImages);
      onImagesChange(updatedImages.map(img => img.id));
      toast.success('Image removed');
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Failed to remove image');
    }
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageUpload(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleImageUpload(e.target.files);
  };

  const handleClickUpload = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      {images.length < maxImages && !disabled && (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={handleClickUpload}
          className={`
            relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-colors duration-200
            ${dragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }
            ${uploading ? 'opacity-50 pointer-events-none' : ''}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/jpeg,image/png,image/gif,image/webp"
            onChange={handleFileInputChange}
            className="hidden"
            disabled={uploading || disabled}
          />

          <div className="flex flex-col items-center space-y-3">
            {uploading ? (
              <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
            ) : (
              <Upload className="w-12 h-12 text-gray-400" />
            )}

            <div>
              <p className="text-lg font-medium text-gray-700">
                {uploading ? 'Uploading...' : 'Click to upload or drag and drop'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                PNG, JPG, GIF, WebP up to 10MB
              </p>
              <p className="text-sm text-gray-500">
                {images.length}/{maxImages} images
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Image Preview Grid */}
      {images.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {images.map((image, index) => (
            <div
              key={image.id}
              className="relative group aspect-square rounded-lg overflow-hidden border-2 border-gray-200 bg-gray-100"
            >
              {/* Image */}
              <Image
                src={image.previewUrl}
                alt={image.originalFilename}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
              />

              {/* Overlay with actions */}
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-200">
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  {!disabled && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveImage(image.id);
                      }}
                      className="p-2 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                      title="Remove image"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Image info */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-2">
                <p className="text-white text-xs truncate" title={image.originalFilename}>
                  {image.originalFilename}
                </p>
                <p className="text-white text-xs opacity-75">
                  {formatFileSize(image.fileSize)}
                </p>
              </div>

              {/* Display order badge */}
              <div className="absolute top-2 left-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                #{index + 1}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info message */}
      {images.length === maxImages && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg text-sm">
          <p className="font-medium">Maximum images reached</p>
          <p>You have uploaded the maximum of {maxImages} images. Remove some to add new ones.</p>
        </div>
      )}
    </div>
  );
}

