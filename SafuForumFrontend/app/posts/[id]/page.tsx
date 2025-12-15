'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Post, Comment, VoteScore, User } from '@/lib/types';
import { postsApi, commentsApi, votesApi, usersApi } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { ArrowUp, ArrowDown, MessageSquare, Edit, Trash2, X } from 'lucide-react';
import Link from 'next/link';
import CommentList from '@/components/CommentList';
import Image from 'next/image';
import toast from 'react-hot-toast';

export default function PostDetail() {
  const params = useParams();
  const router = useRouter();
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentContent, setCommentContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [postVoteScore, setPostVoteScore] = useState<VoteScore>({ score: 0, userVote: null });
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editTags, setEditTags] = useState('');
  const [saving, setSaving] = useState(false);

  // Delete state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchPost();
      fetchComments();
      fetchPostVoteScore();
      fetchCurrentUser();
    }
  }, [params.id]);

  const fetchCurrentUser = async () => {
    try {
      const response = await usersApi.getCurrentUser();
      setCurrentUser(response.data);
    } catch (error) {
      console.log('Not logged in');
    }
  };

  const fetchPost = async () => {
    try {
      const response = await postsApi.getById(Number(params.id));
      setPost(response.data);
      setEditTitle(response.data.title);
      setEditContent(response.data.content);
      setEditTags(response.data.tags?.map(t => t.name).join(', ') || '');
    } catch (error) {
      console.error('Failed to fetch post:', error);
      toast.error('Failed to load post');
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async () => {
    try {
      const response = await commentsApi.getByPost(Number(params.id));
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
      toast.error('Failed to load comments');
    }
  };

  const fetchPostVoteScore = async () => {
    try {
      const response = await votesApi.getPostScore(Number(params.id));
      setPostVoteScore(response.data);
    } catch (error) {
      console.error('Failed to fetch vote score:', error);
    }
  };

  const handleVotePost = async (voteType: number) => {
    try {
      await votesApi.vote({
        postId: Number(params.id),
        voteType: voteType as 1 | -1,
      });
      fetchPostVoteScore();
    } catch (error) {
      console.error('Failed to vote:', error);
      toast.error('Please login to vote');
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentContent.trim()) return;

    try {
      setSubmitting(true);
      await commentsApi.create({
        postId: Number(params.id),
        content: commentContent,
      });
      setCommentContent('');
      fetchComments();
      toast.success('Comment posted!');
    } catch (error) {
      console.error('Failed to create comment:', error);
      toast.error('Please login to comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (parentCommentId: number, content: string) => {
    try {
      await commentsApi.create({
        postId: Number(params.id),
        parentCommentId: parentCommentId,
        content: content,
      });
      fetchComments();
      toast.success('Reply posted!');
    } catch (error) {
      toast.error('Please login to reply');
      throw error;
    }
  };

  const handleStartEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditTitle(post?.title || '');
    setEditContent(post?.content || '');
    setEditTags(post?.tags?.map(t => t.name).join(', ') || '');
  };

  const handleSaveEdit = async () => {
    if (!editTitle.trim() || !editContent.trim()) {
      toast.error('Title and content are required');
      return;
    }

    try {
      setSaving(true);
      await postsApi.update(Number(params.id), {
        title: editTitle,
        content: editContent,
        tags: editTags.split(',').map(t => t.trim()).filter(Boolean),
      });

      setIsEditing(false);
      fetchPost();
      toast.success('Post updated successfully!');
    } catch (error) {
      console.error('Failed to update post:', error);
      toast.error('Failed to update post');
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePost = async () => {
    try {
      setDeleting(true);
      await postsApi.delete(Number(params.id));
      toast.success('Post deleted successfully');
      router.push('/');
    } catch (error) {
      console.error('Failed to delete post:', error);
      toast.error('Failed to delete post');
      setDeleting(false);
    }
  };

  const canEdit = currentUser && post && currentUser.id === post.author.id;
  const canDelete = currentUser && post && (
    currentUser.id === post.author.id ||
    currentUser.role === 'MODERATOR' ||
    currentUser.role === 'ADMIN'
  );

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500 text-lg">Post not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Post Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-6">
        {/* Editing Mode */}
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title
              </label>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content
              </label>
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={8}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={editTags}
                onChange={(e) => setEditTags(e.target.value)}
                placeholder="java, spring-boot, help"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                onClick={handleCancelEdit}
                disabled={saving}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={saving}
                className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Title */}
            <h1 className="text-3xl font-bold text-gray-900 mb-4">{post.title}</h1>

            {/* Meta */}
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-gray-200">
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <div className="flex items-center space-x-2">
                  {post.author.avatarUrl ? (
                    <Image
                      src={post.author.avatarUrl}
                      alt={post.author.displayName || post.author.username}
                      width={40}
                      height={40}
                      className="rounded-full"
                    />
                  ) : (
                    <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {(post.author.displayName || post.author.username)?.charAt(0).toUpperCase() || 'U'}
                    </div>
                  )}
                  <div>
                    <Link
                      href={`/users/${post.author.id}`}
                      className="font-medium text-gray-900 hover:text-primary-600"
                    >
                      {post.author.displayName || post.author.username}
                    </Link>
                    <p className="text-xs text-gray-500">{post.author.reputation} reputation</p>
                  </div>
                </div>
                <span>•</span>
                <span>{formatDistanceToNow(new Date(post.createdAt), { addSuffix: true })}</span>
              </div>

              <div className="flex items-center space-x-2">
                {canEdit && (
                  <button
                    onClick={handleStartEdit}
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Edit post"
                  >
                    <Edit className="w-5 h-5" />
                  </button>
                )}
                {canDelete && (
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete post"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>

            {/* Tags */}
            {post.tags && post.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {post.tags.map((tag) => (
                  <Link
                    key={tag.id}
                    href={`/tags/${tag.slug}`}
                    className="px-3 py-1 text-sm font-medium rounded-full transition-colors hover:opacity-80"
                    style={{
                      backgroundColor: `${tag.color}20`,
                      color: tag.color,
                    }}
                  >
                    {tag.name}
                  </Link>
                ))}
              </div>
            )}

            {/* Content */}
            <div className="prose max-w-none mb-6">
              <p className="text-gray-700 whitespace-pre-wrap">{post.content}</p>
            </div>

            {/* Vote Section */}
            <div className="flex items-center space-x-4 pt-6 border-t border-gray-200">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleVotePost(1)}
                  className={`p-2 rounded-lg transition-colors ${
                    postVoteScore.userVote === 1
                      ? 'text-primary-600 bg-primary-50'
                      : 'text-gray-400 hover:text-primary-600 hover:bg-primary-50'
                  }`}
                >
                  <ArrowUp className="w-5 h-5" />
                </button>
                <span className="font-semibold text-gray-900 min-w-[2rem] text-center">
                  {postVoteScore.score}
                </span>
                <button
                  onClick={() => handleVotePost(-1)}
                  className={`p-2 rounded-lg transition-colors ${
                    postVoteScore.userVote === -1
                      ? 'text-red-600 bg-red-50'
                      : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                  }`}
                >
                  <ArrowDown className="w-5 h-5" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Comments Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <MessageSquare className="w-6 h-6 mr-2" />
          {comments.length} {comments.length === 1 ? 'Comment' : 'Comments'}
        </h2>

        <form onSubmit={handleSubmitComment} className="mb-8">
          <textarea
            value={commentContent}
            onChange={(e) => setCommentContent(e.target.value)}
            placeholder="Write a comment..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            rows={4}
          />
          <div className="flex justify-end mt-3">
            <button
              type="submit"
              disabled={submitting || !commentContent.trim()}
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Posting...' : 'Post Comment'}
            </button>
          </div>
        </form>

        <CommentList
          comments={comments}
          onReply={handleReply}
          onUpdate={fetchComments}
          currentUser={currentUser}
        />
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Delete Post</h3>
              <button
                onClick={() => setShowDeleteModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this post? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeletePost}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete Post'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}