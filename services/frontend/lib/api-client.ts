import axios from 'axios';
import { tokenRefreshService } from './token-refresh-service';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // REMOVED: Don't set Content-Type globally - let axios handle it per request
  withCredentials: true,
});

// Add access token and conditionally set Content-Type
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    // Only set Content-Type to JSON if it's not already set and it's not FormData
    if (!config.headers['Content-Type'] && !(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }

    // If it's FormData, delete Content-Type to let browser set it with boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
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

      const refreshToken = localStorage.getItem('refreshToken');

      // If no refresh token exists, user is simply not logged in
      // Let the request fail gracefully without redirecting
      if (!refreshToken) {
        return Promise.reject(error);
      }

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

        // Use the token refresh service to handle the refresh
        const newAccessToken = await tokenRefreshService.refreshAccessToken();

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed with existing tokens - they're invalid
        // Clear tokens and redirect to home
        console.error('Token refresh failed, logging out:', refreshError);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        tokenRefreshService.stopRefreshMonitoring();

        // Redirect to home page
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