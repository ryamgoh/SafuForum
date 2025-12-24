import axios from 'axios';
import { shouldRefreshToken, isTokenExpired, getTimeUntilExpiry } from './jwt-utils';
import { AuthResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

class TokenRefreshService {
  private refreshTimer: NodeJS.Timeout | null = null;
  private isRefreshing = false;
  private refreshPromise: Promise<string> | null = null;

  /**
   * Initialize proactive token refresh monitoring
   */
  startRefreshMonitoring() {
    if (typeof window === 'undefined') return;

    // Clear any existing timer
    this.stopRefreshMonitoring();

    // Check immediately
    this.checkAndRefreshToken();

    // Set up periodic checks every minute
    this.refreshTimer = setInterval(() => {
      this.checkAndRefreshToken();
    }, 60000); // Check every minute
  }

  /**
   * Stop the token refresh monitoring
   */
  stopRefreshMonitoring() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Check if token needs refresh and refresh if necessary
   */
  private async checkAndRefreshToken() {
    if (typeof window === 'undefined') return;

    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');

    if (!accessToken || !refreshToken) {
      this.stopRefreshMonitoring();
      return;
    }

    // If access token is expired or should be refreshed, do it
    if (isTokenExpired(accessToken) || shouldRefreshToken(accessToken, 5)) {
      console.log('[TokenRefresh] Token needs refresh, refreshing proactively...');
      try {
        await this.refreshAccessToken();
      } catch (error) {
        console.error('[TokenRefresh] Proactive refresh failed:', error);
        // Don't clear tokens here - let the interceptor handle it
      }
    }
  }

  /**
   * Refresh the access token
   * Returns the new access token or throws an error
   */
  async refreshAccessToken(): Promise<string> {
    // If already refreshing, return the existing promise
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;

    this.refreshPromise = this._performRefresh();

    try {
      const newAccessToken = await this.refreshPromise;
      return newAccessToken;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * Actually perform the token refresh API call
   */
  private async _performRefresh(): Promise<string> {
    if (typeof window === 'undefined') {
      throw new Error('Cannot refresh token on server side');
    }

    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post<AuthResponse>(
        `${API_BASE_URL}/api/auth/refresh`,
        { refreshToken },
        {
          headers: { 'Content-Type': 'application/json' },
          withCredentials: true
        }
      );

      const { accessToken, refreshToken: newRefreshToken } = response.data;

      // Save both tokens
      localStorage.setItem('accessToken', accessToken);
      if (newRefreshToken) {
        localStorage.setItem('refreshToken', newRefreshToken);
      }

      console.log('[TokenRefresh] Token refreshed successfully');
      return accessToken;
    } catch (error) {
      console.error('[TokenRefresh] Failed to refresh token:', error);
      throw error;
    }
  }

  /**
   * Check if currently refreshing
   */
  isCurrentlyRefreshing(): boolean {
    return this.isRefreshing;
  }

  /**
   * Get the refresh promise if currently refreshing
   */
  getRefreshPromise(): Promise<string> | null {
    return this.refreshPromise;
  }
}

// Export singleton instance
export const tokenRefreshService = new TokenRefreshService();

