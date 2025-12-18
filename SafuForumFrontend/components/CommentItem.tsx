'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Comment, User } from '@/lib/types';
import { votesApi, commentsApi } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { ArrowUp, ArrowDown, MessageSquare, ChevronDown, ChevronRight, Edit, Trash2, X } from 'lucide-react';
import Image from 'next/image';
import toast from 'react-hot-toast';
import ImageGallery from './ImageGallery';
import ImageUploader from './ImageUploader';

interface CommentItemProps {
  comment: Comment;
  depth?: number;
  onReply: (commentId: number, content: string, imageIds?: number[]) => Promise<void>;
  onUpdate?: () => void;
  currentUser?: User | null;
}

export default function CommentItem({ comment, depth = 0, onReply, onUpdate, currentUser }: CommentItemProps) {
  const [voteScore, setVoteScore] = useState({ score: 0, userVote: null as number | null });
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [replyImageIds, setReplyImageIds] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [saving, setSaving] = useState(false);

  // Delete state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchVoteScore();
  }, [comment.id]);

  const fetchVoteScore = async () => {
    try {
      const response = await votesApi.getCommentScore(comment.id);
      setVoteScore(response.data);
    } catch (error) {
      console.error('Failed to fetch comment vote score:', error);
    }
  };

  const handleVote = async (voteType: 1 | -1) => {
    try {
      await votesApi.vote({
        commentId: comment.id,
        voteType: voteType,
      });
      await fetchVoteScore();
    } catch (error) {
      console.error('Failed to vote on comment:', error);
      toast.error('Please login to vote');
    }
  };

  const handleSubmitReply = async () => {
    if (!replyContent.trim()) return;

    try {
      setSubmitting(true);
      await onReply(comment.id, replyContent, replyImageIds);
      setReplyContent('');
      setReplyImageIds([]);
      setIsReplying(false);
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Failed to submit reply:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartEdit = () => {
    setIsEditing(true);
    setEditContent(comment.content);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditContent(comment.content);
  };

  const handleSaveEdit = async () => {
    if (!editContent.trim()) {
      toast.error('Comment content cannot be empty');
      return;
    }

    try {
      setSaving(true);
      await commentsApi.update(comment.id, { content: editContent });
      setIsEditing(false);
      toast.success('Comment updated successfully!');
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Failed to update comment:', error);
      toast.error('Failed to update comment');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteComment = async () => {
    try {
      setDeleting(true);
      await commentsApi.delete(comment.id);
      toast.success('Comment deleted successfully');
      setShowDeleteModal(false);
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Failed to delete comment:', error);
      toast.error('Failed to delete comment');
      setDeleting(false);
    }
  };

  const hasReplies = comment.replies && comment.replies.length > 0;
  const canEdit = currentUser && currentUser.id === comment.author.id;
  const canDelete = currentUser && (
    currentUser.id === comment.author.id ||
    currentUser.role === 'MODERATOR' ||
    currentUser.role === 'ADMIN'
  );

  return (
    <div className={`${depth > 0 ? 'ml-8 md:ml-12' : ''}`}>
      <div className="border-l-2 border-gray-200 pl-4 md:pl-6 py-3">
        <div className="flex items-start space-x-3">
          {/* Avatar */}
          {comment.author.avatarUrl ? (
            <Image
              src={comment.author.avatarUrl}
              alt={comment.author.displayName || comment.author.username}
              width={32} // w-8
              height={32} // h-8
              className="rounded-full flex-shrink-0"
            />
          ) : (
            <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
              {(comment.author.displayName || comment.author.username)?.charAt(0).toUpperCase() || 'U'}
            </div>
          )}

          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center space-x-2">
                <Link
                  href={`/users/${comment.author.id}`}
                  className="font-medium text-gray-900 hover:text-primary-600 text-sm"
                >
                  {comment.author.displayName || comment.author.username}
                </Link>
                <span className="text-xs text-gray-500">
                  {comment.author.reputation} rep
                </span>
                <span className="text-gray-300">•</span>
                <span className="text-xs text-gray-500">
                  {formatDistanceToNow(new Date(comment.createdAt), { addSuffix: true })}
                </span>
                {comment.updatedAt && comment.updatedAt !== comment.createdAt && (
                  <>
                    <span className="text-gray-300">•</span>
                    <span className="text-xs text-gray-500 italic">edited</span>
                  </>
                )}
              </div>

              {!isEditing && (
                <div className="flex items-center space-x-1">
                  {canEdit && (
                    <button
                      onClick={handleStartEdit}
                      className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                      title="Edit comment"
                    >
                      <Edit className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {canDelete && (
                    <button
                      onClick={() => setShowDeleteModal(true)}
                      className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete comment"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Content */}
            {!isCollapsed && (
              <>
                {isEditing ? (
                  <div className="space-y-2 mb-2">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm resize-none"
                      rows={3}
                    />
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={handleCancelEdit}
                        disabled={saving}
                        className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSaveEdit}
                        disabled={saving || !editContent.trim()}
                        className="px-3 py-1.5 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {saving ? 'Saving...' : 'Save'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="text-gray-700 text-sm mb-2 whitespace-pre-wrap">
                      {comment.content}
                    </p>
                    {/* Images */}
                    {comment.images && comment.images.length > 0 && (
                      <div className="mb-3">
                        <ImageGallery images={comment.images} columns={3} size="small" />
                      </div>
                    )}
                  </>
                )}

                {/* Actions */}
                {!isEditing && (
                  <div className="flex items-center space-x-3 text-sm">
                  {/* Vote buttons */}
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => handleVote(1)}
                      className={`p-1 rounded transition-colors ${
                        voteScore.userVote === 1
                          ? 'text-primary-600 bg-primary-50'
                          : 'text-gray-400 hover:text-primary-600 hover:bg-gray-50'
                      }`}
                    >
                      <ArrowUp className="w-4 h-4" />
                    </button>
                    <span className="font-medium text-gray-600 min-w-[1.5rem] text-center">
                      {voteScore.score}
                    </span>
                    <button
                      onClick={() => handleVote(-1)}
                      className={`p-1 rounded transition-colors ${
                        voteScore.userVote === -1
                          ? 'text-red-600 bg-red-50'
                          : 'text-gray-400 hover:text-red-600 hover:bg-gray-50'
                      }`}
                    >
                      <ArrowDown className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Reply button */}
                  {currentUser ? (
                    <button
                      onClick={() => setIsReplying(!isReplying)}
                      className="text-gray-500 hover:text-primary-600 font-medium flex items-center space-x-1"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>{isReplying ? 'Cancel' : 'Reply'}</span>
                    </button>
                  ) : (
                    <button
                      disabled
                      className="text-gray-400 font-medium flex items-center space-x-1 cursor-not-allowed"
                      title="Please log in to reply"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Reply</span>
                    </button>
                  )}

                  {/* Collapse button (only if has replies) */}
                  {hasReplies && (
                    <button
                      onClick={() => setIsCollapsed(!isCollapsed)}
                      className="text-gray-500 hover:text-gray-700 flex items-center space-x-1"
                    >
                      <ChevronDown className="w-3.5 h-3.5" />
                      <span>Collapse</span>
                    </button>
                  )}
                  </div>
                )}

                {/* Reply Form */}
                {isReplying && (
                  <div className="mt-3">
                    <textarea
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                      placeholder="Write a reply..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm resize-none"
                      rows={3}
                    />
                    <div className="mt-2">
                      <ImageUploader
                        maxImages={3}
                        onImagesChange={setReplyImageIds}
                        disabled={submitting}
                      />
                    </div>
                    <div className="flex justify-end space-x-2 mt-2">
                      <button
                        type="button"
                        onClick={() => {
                          setIsReplying(false);
                          setReplyContent('');
                          setReplyImageIds([]);
                        }}
                        className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSubmitReply}
                        disabled={!replyContent.trim() || submitting}
                        className="px-3 py-1.5 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {submitting ? 'Posting...' : 'Reply'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Collapsed state */}
            {isCollapsed && hasReplies && (
              <button
                onClick={() => setIsCollapsed(false)}
                className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center space-x-1"
              >
                <ChevronRight className="w-3 h-3" />
                <span>
                  Show {comment.replies!.length} {comment.replies!.length === 1 ? 'reply' : 'replies'}
                </span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Nested Replies */}
      {!isCollapsed && hasReplies && (
        <div className="mt-1">
          {comment.replies!.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              depth={depth + 1}
              onReply={onReply}
              onUpdate={onUpdate}
              currentUser={currentUser}
            />
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Delete Comment</h3>
              <button
                onClick={() => setShowDeleteModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this comment? This action cannot be undone.
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
                onClick={handleDeleteComment}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete Comment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}