import axios from 'axios';
import { tokenRefreshService } from './token-refresh-service';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add access token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only handle 401 errors and avoid infinite retry loops
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Check if already refreshing to avoid race conditions
        if (tokenRefreshService.isCurrentlyRefreshing()) {
          // Wait for the ongoing refresh to complete
          const newAccessToken = await tokenRefreshService.getRefreshPromise();
          if (newAccessToken) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiClient(originalRequest);
          }
        }

        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          // Use the token refresh service to handle the refresh
          const newAccessToken = await tokenRefreshService.refreshAccessToken();

          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        } else {
          // No refresh token available
          throw new Error('No refresh token available');
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to home
        console.error('Token refresh failed, logging out:', refreshError);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        tokenRefreshService.stopRefreshMonitoring();

        // Redirect to home page instead of non-existent /login
        if (typeof window !== 'undefined') {
          window.location.href = '/';
        }

        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

