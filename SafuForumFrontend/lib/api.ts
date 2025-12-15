import apiClient from './api-client';
import {
  Post,
  Comment,
  User,
  VoteScore,
  CreatePostRequest,
  UpdatePostRequest,
  CreateCommentRequest,
  UpdateCommentRequest,
  VoteRequest,
  PaginatedResponse,
  Tag,
  AuthResponse,
  RefreshTokenRequest,
} from './types';

// Posts API
export const postsApi = {
  getAll: (page = 0, size = 20) =>
    apiClient.get<PaginatedResponse<Post>>('/api/posts', { params: { page, size } }),

  getTrending: (page = 0, size = 20, days = 7) =>
    apiClient.get<PaginatedResponse<Post>>('/api/posts/trending', { params: { page, size, days } }),

  getMostDiscussed: (page = 0, size = 20) =>
    apiClient.get<PaginatedResponse<Post>>('/api/posts/discussed', { params: { page, size } }),

  getHot: (page = 0, size = 20) =>
    apiClient.get<PaginatedResponse<Post>>('/api/posts/hot', { params: { page, size } }),

  getByTag: (tagSlug: string, page = 0, size = 20) =>
    apiClient.get<PaginatedResponse<Post>>(`/api/posts/tag/${tagSlug}`, { params: { page, size } }),

  getById: (id: number) =>
    apiClient.get<Post>(`/api/posts/${id}`),

  getByUser: (userId: number, page = 0, size = 20) =>
    apiClient.get<PaginatedResponse<Post>>(`/api/posts/user/${userId}`, { params: { page, size } }),

  create: (data: CreatePostRequest) =>
    apiClient.post<Post>('/api/posts', data),

  update: (id: number, data: UpdatePostRequest) =>
    apiClient.put<Post>(`/api/posts/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/api/posts/${id}`),
};
// Comments API
export const commentsApi = {
  getByPost: (postId: number) =>
    apiClient.get<Comment[]>(`/api/comments/post/${postId}`),

  getById: (id: number) => apiClient.get<Comment>(`/api/comments/${id}`),

  getByUser: (userId: number) =>
    apiClient.get<Comment[]>(`/api/comments/user/${userId}`),

  create: (data: CreateCommentRequest) =>
    apiClient.post<Comment>('/api/comments', data),

  update: (id: number, data: UpdateCommentRequest) =>
    apiClient.put<Comment>(`/api/comments/${id}`, data),

  delete: (id: number) => apiClient.delete(`/api/comments/${id}`),
};

// Votes API
export const votesApi = {
  vote: (data: VoteRequest) => apiClient.post('/api/votes', data),

  removeVote: (postId?: number, commentId?: number) =>
    apiClient.delete('/api/votes', {
      params: { postId, commentId },
    }),

  getPostScore: (postId: number) =>
    apiClient.get<VoteScore>(`/api/votes/post/${postId}`),

  getCommentScore: (commentId: number) =>
    apiClient.get<VoteScore>(`/api/votes/comment/${commentId}`),
};

// Users API
export const usersApi = {
  getById: (id: number) => apiClient.get<User>(`/api/users/${id}`),

  getCurrentUser: () => apiClient.get<User>('/api/users/me'),
};

// Auth API
export const authApi = {
  logout: (refreshToken: string) =>
    apiClient.post('/api/auth/logout', { refreshToken }),

  logoutAll: () => apiClient.post('/api/auth/logout-all'),

  refresh: (refreshToken: string) =>
    apiClient.post('/api/auth/refresh', { refreshToken }),
};

// Tags API
export const tagsApi = {
  getAll: () => apiClient.get<Tag[]>('/api/tags'),

  getBySlug: (slug: string) => apiClient.get<Tag>(`/api/tags/${slug}`),
};