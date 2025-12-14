'use client';

import { Comment } from '@/lib/types';
import CommentItem from './CommentItem';

interface CommentListProps {
  comments: Comment[];
  onReply: (commentId: number, content: string) => Promise<void>;
}

export default function CommentList({ comments, onReply }: CommentListProps) {
  if (comments.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No comments yet. Be the first to comment!</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {comments.map((comment) => (
        <CommentItem key={comment.id} comment={comment} onReply={onReply} />
      ))}
    </div>
  );
}