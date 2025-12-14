'use client';

import { useEffect, useState } from 'react';
import { Post } from '@/lib/types';
import { postsApi } from '@/lib/api';
import PostCard from '@/components/PostCard';
import { TrendingUp } from 'lucide-react';

export default function TrendingPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrendingPosts();
  }, []);

  const fetchTrendingPosts = async () => {
    try {
      const response = await postsApi.getTrending(0, 20, 7);
      setPosts(response.data.content);
    } catch (error) {
      console.error('Failed to fetch trending posts:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="max-w-5xl mx-auto px-6 py-8">Loading...</div>;
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center space-x-3 mb-8">
        <TrendingUp className="w-8 h-8 text-orange-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trending Posts</h1>
          <p className="text-gray-600">Most upvoted posts in the last 7 days</p>
        </div>
      </div>

      <div className="space-y-4">
        {posts.length === 0 ? (
          <p className="text-gray-500 text-center py-12">No trending posts yet</p>
        ) : (
          posts.map((post) => <PostCard key={post.id} post={post} />)
        )}
      </div>
    </div>
  );
}