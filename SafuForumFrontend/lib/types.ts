// User types
export interface User {
  id: number;
  username: string;
  email: string;
  displayName?: string;
  avatarUrl?: string;
  bio?: string;
  reputation: number;
  role: 'USER' | 'MODERATOR' | 'ADMIN' | 'TRUSTED_USER';
  oauthProvider?: string;
  oauthProviderId?: string;
  createdAt: string;
  lastLoginAt?: string;
}

// Post types
export interface Post {
  id: number;
  title: string;
  content: string;
  authorId: number;
  author: User;
  viewCount: number;
  commentCount: number;
  tags?: Tag[];
  createdAt: string;
  updatedAt: string;
  editedAt?: string;
}

export interface CreatePostRequest {
  title: string;
  content: string;
  tags?: string[];
}

export interface UpdatePostRequest {
  title?: string;
  content?: string;
  tags?: string[];
}

// Comment types
export interface Comment {
  id: number;
  content: string;
  postId: number;
  authorId: number;
  author: User;
  parentCommentId?: number;
  replies?: Comment[];
  createdAt: string;
  updatedAt: string;
  editedAt?: string;
}

export interface CreateCommentRequest {
  content: string;
  postId: number;
  parentCommentId?: number;
}

export interface UpdateCommentRequest {
  content: string;
}

// Vote types
export interface VoteScore {
  score: number;
  userVote: number | null; // 1 for upvote, -1 for downvote, null for no vote
}

export interface VoteRequest {
  postId?: number;
  commentId?: number;
  voteType: 1 | -1; // 1 for upvote, -1 for downvote
}

// Tag types
export interface Tag {
  id: number;
  name: string;
  slug: string;
  color: string;
  postCount: number;
}

// Auth types
export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number; // seconds
  userId: number;
  username: string;
  role: string;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

// Pagination types
export interface PaginatedResponse<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  last: boolean;
  first: boolean;
}

// Moderation types (if needed later)
export interface ModerationAction {
  id: number;
  moderatorId: number;
  targetType: 'POST' | 'COMMENT' | 'USER';
  targetId: number;
  actionType: string;
  reason: string;
  createdAt: string;
}

export interface ContentFlag {
  id: number;
  reporterId: number;
  targetType: 'POST' | 'COMMENT';
  targetId: number;
  reason: string;
  status: 'PENDING' | 'REVIEWED' | 'RESOLVED';
  createdAt: string;
}

