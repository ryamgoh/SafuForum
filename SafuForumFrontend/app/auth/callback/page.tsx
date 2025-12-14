'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { tokenRefreshService } from '@/lib/token-refresh-service';
import toast from 'react-hot-toast';

function CallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const accessToken = searchParams.get('accessToken');
    const refreshToken = searchParams.get('refreshToken');

    if (accessToken && refreshToken) {
      try {
        // Store tokens in localStorage
        localStorage.setItem('accessToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);

        // Start proactive token refresh monitoring
        tokenRefreshService.startRefreshMonitoring();

        // Show success message
        toast.success('Successfully logged in!');

        // Redirect to home page
        router.push('/');
      } catch (error) {
        console.error('Failed to store tokens:', error);
        toast.error('Authentication failed. Please try again.');
        router.push('/?error=storage_failed');
      }
    } else {
      console.error('No tokens received from OAuth callback');
      toast.error('Authentication failed. No tokens received.');
      // Redirect to home with error
      router.push('/?error=auth_failed');
    }
  }, [searchParams, router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Completing login...</h2>
        <p className="text-gray-600">Please wait while we authenticate you</p>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600"></div>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}