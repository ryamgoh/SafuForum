'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Post } from '@/lib/types';
import { votesApi } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { MessageSquare, Eye, ArrowUp, ArrowDown } from 'lucide-react';
import Image from 'next/image';
import toast from 'react-hot-toast';

interface PostCardProps {
  post: Post;
}

export default function PostCard({ post }: PostCardProps) {
  const [voteScore, setVoteScore] = useState({ score: 0, userVote: null as number | null });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchVoteScore();
  }, [post.id]);

  const fetchVoteScore = async () => {
    try {
      const response = await votesApi.getPostScore(post.id);
      setVoteScore(response.data);
    } catch (error) {
      console.error('Failed to fetch vote score:', error);
    }
  };

  const handleVote = async (voteType: 1 | -1, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (loading) return;

    try {
      setLoading(true);
      await votesApi.vote({
        postId: post.id,
        voteType: voteType,
      });
      await fetchVoteScore();
    } catch (error) {
      console.error('Failed to vote:', error);
      toast.error('Please login to vote');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex space-x-4">
        {/* Vote Section */}
        <div className="flex flex-col items-center space-y-2">
          <button
            onClick={(e) => handleVote(1, e)}
            disabled={loading}
            className={`p-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              voteScore.userVote === 1
                ? 'text-primary-600 bg-primary-50'
                : 'text-gray-400 hover:text-primary-600 hover:bg-gray-100'
            }`}
          >
            <ArrowUp className="w-6 h-6" />
          </button>
          <span
            className={`font-semibold text-lg ${
              voteScore.score > 0
                ? 'text-primary-600'
                : voteScore.score < 0
                ? 'text-red-600'
                : 'text-gray-600'
            }`}
          >
            {voteScore.score}
          </span>
          <button
            onClick={(e) => handleVote(-1, e)}
            disabled={loading}
            className={`p-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              voteScore.userVote === -1
                ? 'text-red-600 bg-red-50'
                : 'text-gray-400 hover:text-red-600 hover:bg-gray-100'
            }`}
          >
            <ArrowDown className="w-6 h-6" />
          </button>
        </div>

        {/* Content Section */}
        <div className="flex-1 min-w-0">
          <Link href={`/posts/${post.id}`}>
            <h2 className="text-xl font-semibold text-gray-900 hover:text-primary-600 transition-colors mb-2">
              {post.title}
            </h2>
          </Link>

          <p className="text-gray-600 mb-4 line-clamp-2">{post.content}</p>

          {/* Tags */}
          {post.tags && post.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {post.tags.map((tag) => (
                <Link
                  key={tag.id}
                  href={`/tags/${tag.slug}`}
                  className="px-3 py-1 text-xs font-medium rounded-full transition-colors hover:opacity-80"
                  style={{
                    backgroundColor: `${tag.color}20`,
                    color: tag.color,
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {tag.name}
                </Link>
              ))}
            </div>
          )}

          {/* Meta Info */}
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {post.author.avatarUrl ? (
                  <Image
                    src={post.author.avatarUrl}
                    alt={post.author.displayName || post.author.username}
                    width={24} // w-6
                    height={24} // h-6
                    className="rounded-full"
                  />
                ) : (
                  <div className="w-6 h-6 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                    {(post.author.displayName || post.author.username)
                      .charAt(0)
                      .toUpperCase()}
                  </div>
                )}
                <Link
                  href={`/users/${post.author.id}`}
                  className="font-medium text-gray-700 hover:text-primary-600"
                  onClick={(e) => e.stopPropagation()}
                >
                  {post.author.displayName || post.author.username}
                </Link>
                <span>•</span>
                <span>{post.author.reputation} rep</span>
              </div>
              <span>•</span>
              <span>
                {formatDistanceToNow(new Date(post.createdAt), {
                  addSuffix: true,
                })}
              </span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                <MessageSquare className="w-4 h-4" />
                <span>0</span>
              </div>
              <div className="flex items-center space-x-1">
                <Eye className="w-4 h-4" />
                <span>0</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}