'use client';

import { useEffect, useState } from 'react';
import { Post } from '@/lib/types';
import { postsApi } from '@/lib/api';
import PostCard from '@/components/PostCard';
import { TrendingUp, Clock, MessageSquare } from 'lucide-react';

const sortOptions = [
  { label: 'Recent', value: 'recent', icon: Clock },
  { label: 'Trending', value: 'trending', icon: TrendingUp },
  { label: 'Most Discussed', value: 'discussed', icon: MessageSquare },
];

export default function Home() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSort, setSelectedSort] = useState('recent');
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    fetchPosts();
  }, [selectedSort, page]);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      let response;

      switch (selectedSort) {
        case 'trending':
          response = await postsApi.getTrending(page, 20, 7);
          break;
        case 'discussed':
          response = await postsApi.getMostDiscussed(page, 20);
          break;
        default:
          response = await postsApi.getAll(page, 20);
          break;
      }

      setPosts(response.data.content);
      setTotalPages(response.data.totalPages);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSortChange = (sortValue: string) => {
    setSelectedSort(sortValue);
    setPage(0);
  };

  if (loading) {
    return <div className="max-w-5xl mx-auto px-6 py-8">Loading...</div>;
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Discussion Board</h1>
        <p className="text-gray-600">Share and discuss topics with the community</p>
      </div>

      <div className="flex items-center space-x-2 mb-6">
        {sortOptions.map((option) => {
          const Icon = option.icon;
          return (
            <button
              key={option.value}
              onClick={() => handleSortChange(option.value)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedSort === option.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{option.label}</span>
            </button>
          );
        })}
      </div>

      {posts.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500 text-lg mb-4">No posts yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2 mt-8">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-4 py-2 bg-white border border-gray-200 rounded-lg"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-gray-600">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="px-4 py-2 bg-white border border-gray-200 rounded-lg"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}