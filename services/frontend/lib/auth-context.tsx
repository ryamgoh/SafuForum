'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User } from './types';
import { usersApi, authApi } from './api';
import { tokenRefreshService } from './token-refresh-service';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch current user
  const fetchUser = useCallback(async () => {
    if (typeof window === 'undefined') return;

    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');

    if (!accessToken || !refreshToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response = await usersApi.getCurrentUser();
      setUser(response.data);

      // Start proactive token refresh monitoring
      tokenRefreshService.startRefreshMonitoring();
    } catch (error: any) {
      console.error('Failed to fetch current user:', error);

      // If 401, tokens are invalid - clear them
      if (error.response?.status === 401) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setUser(null);
        tokenRefreshService.stopRefreshMonitoring();
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Initialize auth state on mount
  useEffect(() => {
    fetchUser();

    // Cleanup on unmount
    return () => {
      tokenRefreshService.stopRefreshMonitoring();
    };
  }, [fetchUser]);

  // Login function - redirects to OAuth
  const login = useCallback(() => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8081';
    window.location.href = `${API_BASE_URL}/oauth2/authorization/google`;
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');

      if (refreshToken) {
        // Call logout endpoint to revoke token
        await authApi.logout(refreshToken);
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API fails
    } finally {
      // Clear local storage and state
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      setUser(null);

      // Stop token refresh monitoring
      tokenRefreshService.stopRefreshMonitoring();

      // Redirect to home
      window.location.href = '/';
    }
  }, []);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

