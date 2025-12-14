'use client';

import { useEffect, useState } from 'react';
import { Tag, Hash } from 'lucide-react';
import Link from 'next/link';
import { tagsApi } from '@/lib/api';
import toast from 'react-hot-toast';

interface TagWithCount {
  id: number;
  name: string;
  slug: string;
  color: string;
  postCount?: number;
}

export default function TagsPage() {
  const [tags, setTags] = useState<TagWithCount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTags();
  }, []);

  const fetchTags = async () => {
    try {
      const response = await tagsApi.getAll();
      setTags(response.data);
    } catch (error) {
      console.error('Failed to fetch tags:', error);
      toast.error('Failed to load tags');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
              <div className="flex items-start justify-between mb-3">
                <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                <div className="w-16 h-6 bg-gray-200 rounded-full"></div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
          <Tag className="w-8 h-8 mr-3 text-primary-600" />
          Tags
        </h1>
        <p className="text-gray-600">
          Browse topics by category • {tags.length} {tags.length === 1 ? 'tag' : 'tags'}
        </p>
      </div>

      {/* No Tags State */}
      {tags.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Tag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg mb-2">No tags yet</p>
          <p className="text-gray-400">Tags will appear here when posts are created</p>
        </div>
      ) : (
        /* Tags Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tags.map((tag) => (
            <Link
              key={tag.id}
              href={`/tags/${tag.slug}`}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-primary-300 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="w-12 h-12 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${tag.color}20` }}
                >
                  <Hash className="w-6 h-6" style={{ color: tag.color }} />
                </div>
                {tag.postCount !== undefined && (
                  <span
                    className="px-3 py-1 rounded-full text-xs font-semibold"
                    style={{
                      backgroundColor: `${tag.color}15`,
                      color: tag.color,
                    }}
                  >
                    {tag.postCount} {tag.postCount === 1 ? 'post' : 'posts'}
                  </span>
                )}
              </div>
              <h3
                className="text-lg font-semibold mb-1 group-hover:underline"
                style={{ color: tag.color }}
              >
                {tag.name}
              </h3>
              <p className="text-sm text-gray-500">
                Explore {tag.name.toLowerCase()} discussions
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}