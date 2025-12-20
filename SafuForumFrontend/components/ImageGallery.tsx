'use client';

import { useState } from 'react';
import { ImageResponse } from '@/lib/types';
import { getImageUrl } from '@/lib/image-utils';
import Image from 'next/image';
import ImageModal from './ImageModal';

interface ImageGalleryProps {
  images: ImageResponse[];
  columns?: 2 | 3 | 4;
  size?: 'small' | 'medium' | 'large';
}

export default function ImageGallery({
  images,
  columns = 3,
  size = 'medium'
}: ImageGalleryProps) {
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(null);

  if (!images || images.length === 0) {
    return null;
  }

  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-2 md:grid-cols-3',
    4: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
  };

  const aspectRatio = {
    small: 'aspect-video',
    medium: 'aspect-square',
    large: 'aspect-[4/3]'
  };

  const handleImageClick = (index: number) => {
    setSelectedImageIndex(index);
  };

  const handleCloseModal = () => {
    setSelectedImageIndex(null);
  };

  const handleNextImage = () => {
    if (selectedImageIndex !== null) {
      setSelectedImageIndex((selectedImageIndex + 1) % images.length);
    }
  };

  const handlePrevImage = () => {
    if (selectedImageIndex !== null) {
      setSelectedImageIndex((selectedImageIndex - 1 + images.length) % images.length);
    }
  };

  return (
    <>
      <div className={`grid ${gridCols[columns]} gap-4`}>
        {images.map((image, index) => (
          <button
            key={image.id}
            onClick={() => handleImageClick(index)}
            className={`
              relative ${aspectRatio[size]} rounded-lg overflow-hidden
              border border-gray-200 hover:border-primary-400
              transition-all hover:shadow-lg cursor-pointer
              group bg-gray-100
            `}
          >
            <Image
              src={getImageUrl(image.url)}
              alt={image.originalFilename}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
              sizes={`(max-width: 768px) 50vw, (max-width: 1024px) ${100 / columns}vw, ${100 / columns}vw`}
            />

            {/* Hover overlay */}
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200" />

            {/* Image number badge */}
            {images.length > 1 && (
              <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                {index + 1}/{images.length}
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Lightbox Modal */}
      {selectedImageIndex !== null && (
        <ImageModal
          images={images}
          currentIndex={selectedImageIndex}
          onClose={handleCloseModal}
          onNext={handleNextImage}
          onPrev={handlePrevImage}
        />
      )}
    </>
  );
}

