'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { postsApi } from '@/lib/api';
import { ArrowLeft, X } from 'lucide-react';
import Link from 'next/link';
import ImageUploader from '@/components/ImageUploader';

export default function NewPost() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [imageIds, setImageIds] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!tags.includes(tagInput.trim())) {
        setTags([...tags, tagInput.trim()]);
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    if (title.length < 3 || title.length > 300) {
      setError('Title must be between 3 and 300 characters');
      return;
    }

    if (!content.trim()) {
      setError('Content is required');
      return;
    }

    if (content.length < 10) {
      setError('Content must be at least 10 characters');
      return;
    }

    try {
      setSubmitting(true);
      const response = await postsApi.create({
        title: title.trim(),
        content: content.trim(),
        tags: tags.length > 0 ? tags : undefined,
        imageIds: imageIds.length > 0 ? imageIds : undefined,
      });
      router.push(`/posts/${response.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create post');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center space-x-2 text-gray-600 hover:text-primary-600 mb-4"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Home</span>
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Create New Post</h1>
        <p className="text-gray-600">Share your thoughts with the community</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Title */}
        <div className="mb-6">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a descriptive title..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            maxLength={300}
          />
          <p className="text-sm text-gray-500 mt-1">{title.length}/300 characters</p>
        </div>

        {/* Content */}
        <div className="mb-6">
          <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
            Content <span className="text-red-500">*</span>
          </label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your post content here..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows={12}
          />
          <p className="text-sm text-gray-500 mt-1">
            {content.length} characters (minimum 10)
          </p>
        </div>

        {/* Images */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Images
          </label>
          <ImageUploader
            maxImages={10}
            onImagesChange={setImageIds}
            disabled={submitting}
          />
          <p className="text-sm text-gray-500 mt-2">
            Upload up to 10 images (PNG, JPG, GIF, WebP, max 10MB each)
          </p>
        </div>

        {/* Tags */}
        <div className="mb-8">
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
            Tags
          </label>
          <input
            type="text"
            id="tags"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleAddTag}
            placeholder="Type and press Enter to add tags..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <p className="text-sm text-gray-500 mt-1">Press Enter to add a tag</p>

          {/* Tag List */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center space-x-2 bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-medium"
                >
                  <span>{tag}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-primary-900"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-6 border-t border-gray-200">
          <Link
            href="/"
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-lg transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Creating...' : 'Create Post'}
          </button>
        </div>
      </form>
    </div>
  );
}

