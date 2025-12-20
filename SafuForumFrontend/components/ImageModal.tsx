'use client';

import { useEffect, useCallback } from 'react';
import { ImageResponse } from '@/lib/types';
import { getImageUrl, formatFileSize } from '@/lib/image-utils';
import { X, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import Image from 'next/image';

interface ImageModalProps {
  images: ImageResponse[];
  currentIndex: number;
  onClose: () => void;
  onNext: () => void;
  onPrev: () => void;
}

export default function ImageModal({
  images,
  currentIndex,
  onClose,
  onNext,
  onPrev
}: ImageModalProps) {
  const currentImage = images[currentIndex];
  const hasMultiple = images.length > 1;

  // Keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowRight' && hasMultiple) {
      onNext();
    } else if (e.key === 'ArrowLeft' && hasMultiple) {
      onPrev();
    }
  }, [onClose, onNext, onPrev, hasMultiple]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [handleKeyDown]);

  const handleDownload = async () => {
    try {
      const response = await fetch(getImageUrl(currentImage.url));
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = currentImage.originalFilename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black bg-opacity-95 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors z-10"
        title="Close (Esc)"
      >
        <X className="w-6 h-6" />
      </button>

      {/* Previous button */}
      {hasMultiple && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPrev();
          }}
          className="absolute left-4 p-3 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors z-10"
          title="Previous (←)"
        >
          <ChevronLeft className="w-8 h-8" />
        </button>
      )}

      {/* Next button */}
      {hasMultiple && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onNext();
          }}
          className="absolute right-4 p-3 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors z-10"
          title="Next (→)"
        >
          <ChevronRight className="w-8 h-8" />
        </button>
      )}

      {/* Image container */}
      <div
        className="relative max-w-7xl max-h-[90vh] w-full h-full flex items-center justify-center p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative w-full h-full">
          <Image
            src={getImageUrl(currentImage.url)}
            alt={currentImage.originalFilename}
            fill
            className="object-contain"
            sizes="100vw"
            priority
          />
        </div>
      </div>

      {/* Image info bar */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-6 text-white">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-lg font-medium truncate">
              {currentImage.originalFilename}
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-300 mt-1">
              <span>{formatFileSize(currentImage.fileSize)}</span>
              {hasMultiple && (
                <>
                  <span>•</span>
                  <span>
                    {currentIndex + 1} of {images.length}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Download button */}
          <button
            onClick={handleDownload}
            className="ml-4 p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
            title="Download"
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Navigation hints */}
      {hasMultiple && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 text-white text-sm bg-black bg-opacity-50 px-4 py-2 rounded-full">
          Use arrow keys to navigate
        </div>
      )}
    </div>
  );
}

