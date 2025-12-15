'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Tag as TagIcon, Hash } from 'lucide-react';
import { tagsApi, postsApi } from '@/lib/api';
import { Post, Tag } from '@/lib/types';
import PostCard from '@/components/PostCard';
import toast from 'react-hot-toast';


export default function TagDetailPage() {
  const params = useParams();
  const [tag, setTag] = useState<Tag | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    if (params.slug) {
      fetchTag();
      fetchPosts();
    }
  }, [params.slug, page]);

  const fetchTag = async () => {
    try {
      const response = await tagsApi.getBySlug(params.slug as string);
      setTag(response.data);
    } catch (error) {
      console.error('Failed to fetch tag:', error);
      toast.error('Failed to load tag');
    }
  };

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await postsApi.getByTag(params.slug as string, page, 20);

      if (page === 0) {
        setPosts(response.data.content);
      } else {
        setPosts(prev => [...prev, ...response.data.content]);
      }

      setHasMore(!response.data.last);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
      toast.error('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
    }
  };

  if (loading && page === 0) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8 animate-pulse">
          <div className="h-10 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-6 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!tag) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <TagIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">Tag not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <div
            className="w-16 h-16 rounded-lg flex items-center justify-center mr-4"
            style={{ backgroundColor: `${tag.color}20` }}
          >
            <Hash className="w-8 h-8" style={{ color: tag.color }} />
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{ color: tag.color }}>
              {tag.name}
            </h1>
            <p className="text-gray-600 mt-1">
              {posts.length} {posts.length === 1 ? 'post' : 'posts'}
            </p>
          </div>
        </div>
      </div>

      {/* Posts List */}
      {posts.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <TagIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg mb-2">No posts yet</p>
          <p className="text-gray-400">Be the first to create a post with this tag!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}

          {/* Load More Button */}
          {hasMore && (
            <div className="flex justify-center pt-6">
              <button
                onClick={loadMore}
                disabled={loading}
                className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}