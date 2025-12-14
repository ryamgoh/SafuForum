'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Comment } from '@/types';
import { votesApi } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { ArrowUp, ArrowDown, MessageSquare, ChevronDown, ChevronRight } from 'lucide-react';
import Image from 'next/image';

interface CommentItemProps {
  comment: Comment;
  depth?: number;
  onReply: (commentId: number, content: string) => Promise<void>;
}

export default function CommentItem({ comment, depth = 0, onReply }: CommentItemProps) {
  const [voteScore, setVoteScore] = useState({ score: 0, userVote: null as number | null });
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

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
      alert('Please login to vote');
    }
  };

  const handleSubmitReply = async () => {
    if (!replyContent.trim()) return;

    try {
      setSubmitting(true);
      await onReply(comment.id, replyContent);
      setReplyContent('');
      setIsReplying(false);
    } catch (error) {
      console.error('Failed to submit reply:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const hasReplies = comment.replies && comment.replies.length > 0;

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
            <div className="flex items-center space-x-2 mb-1">
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
            </div>

            {/* Content */}
            {!isCollapsed && (
              <>
                <p className="text-gray-700 text-sm mb-2 whitespace-pre-wrap">
                  {comment.content}
                </p>

                {/* Actions */}
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
                  <button
                    onClick={() => setIsReplying(!isReplying)}
                    className="text-gray-500 hover:text-primary-600 font-medium flex items-center space-x-1"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>{isReplying ? 'Cancel' : 'Reply'}</span>
                  </button>

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
                    <div className="flex justify-end space-x-2 mt-2">
                      <button
                        onClick={() => {
                          setIsReplying(false);
                          setReplyContent('');
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
            />
          ))}
        </div>
      )}
    </div>
  );
}