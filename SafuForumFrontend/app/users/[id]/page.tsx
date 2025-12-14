'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { User, Post } from '@/types';
import { usersApi, postsApi } from '@/lib/api';
import PostCard from '@/components/PostCard';
import { Calendar, Award, MessageSquare, FileText } from 'lucide-react';
import Image from 'next/image';

export default function UserProfilePage() {
  const params = useParams();
  const userId = parseInt(params.id as string);

  const [user, setUser] = useState<User | null>(null);
  const [userPosts, setUserPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserData();
  }, [userId]);

  const fetchUserData = async () => {
    try {
      setLoading(true);

      // Fetch user info
      const userResponse = await usersApi.getById(userId);
      setUser(userResponse.data);

      // Fetch user's posts
      const postsResponse = await postsApi.getByUser(userId, 0, 20);
      setUserPosts(postsResponse.data.content);
    } catch (error) {
      console.error('Failed to fetch user data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 rounded-lg mb-6"></div>
          <div className="space-y-4">
            <div className="h-24 bg-gray-200 rounded-lg"></div>
            <div className="h-24 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">User not found</p>
        </div>
      </div>
    );
  }

  const formattedDate = new Date(user.createdAt).toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  });

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-6">
        <div className="flex items-start space-x-6">
          {/* Avatar */}
          {user.avatarUrl ? (
            <Image
              src={user.avatarUrl}
              alt={user.username}
              width={96}
              height={96}
              className="rounded-full"
            />
          ) : (
            <div className="w-24 h-24 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-3xl font-bold">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
          )}

          {/* User Info */}
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {user.displayName || user.username}
            </h1>
            <p className="text-gray-600 mb-4">@{user.username}</p>

            {/* Stats */}
            <div className="flex items-center space-x-6 mb-4">
              <div className="flex items-center space-x-2 text-gray-700">
                <Award className="w-5 h-5 text-yellow-500" />
                <span className="font-semibold">{user.reputation}</span>
                <span className="text-gray-500">reputation</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-700">
                <FileText className="w-5 h-5 text-blue-500" />
                <span className="font-semibold">{userPosts.length}</span>
                <span className="text-gray-500">posts</span>
              </div>
              <div className="flex items-center space-x-2 text-gray-700">
                <Calendar className="w-5 h-5 text-gray-400" />
                <span className="text-gray-500">Joined {formattedDate}</span>
              </div>
            </div>

            {/* Role Badge */}
            <div className="flex items-center space-x-2">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  user.role === 'ADMIN'
                    ? 'bg-red-100 text-red-800'
                    : user.role === 'MODERATOR'
                    ? 'bg-purple-100 text-purple-800'
                    : user.role === 'TRUSTED_USER'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {user.role.replace('_', ' ')}
              </span>
            </div>

            {/* Bio */}
            {user.bio && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-700">{user.bio}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* User's Posts */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
          <MessageSquare className="w-6 h-6 mr-2 text-primary-600" />
          Posts by {user.displayName || user.username}
        </h2>
      </div>

      {userPosts.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">No posts yet</p>
          <p className="text-gray-400 mt-2">This user hasn't created any posts</p>
        </div>
      ) : (
        <div className="space-y-4">
          {userPosts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}