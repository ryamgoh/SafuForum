'use client';

import Image from 'next/image';
import { Home, TrendingUp, Tag, Users, Settings, LogOut, Plus, LogIn } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { User } from '@/lib/types';

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Trending', href: '/trending', icon: TrendingUp },
  { name: 'Tags', href: '/tags', icon: Tag },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user: currentUser, loading, login, logout } = useAuth();

  const getUserInitials = (user: User) => {
    if (user.displayName) {
      return user.displayName
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    return user.username.slice(0, 2).toUpperCase();
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <Link href="/">
          <h1 className="text-2xl font-bold text-primary-600 cursor-pointer">SafuForum</h1>
          <p className="text-sm text-gray-500 mt-1">University Community</p>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Create Post Button */}
      {currentUser && (
        <div className="p-4 border-t border-gray-200">
          <Link
            href="/posts/new"
            className="flex items-center justify-center space-x-2 w-full bg-primary-600 hover:bg-primary-700 text-white font-medium px-4 py-3 rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>New Post</span>
          </Link>
        </div>
      )}

      {/* User Section */}
      <div className="p-4 border-t border-gray-200">
        {loading ? (
          <div className="animate-pulse">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
          </div>
        ) : currentUser ? (
          <>
            <Link href={`/users/${currentUser.id}`}>
              <div className="flex items-center space-x-3 mb-3 cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition-colors">
                {currentUser.avatarUrl ? (
                  <Image
                    src={currentUser.avatarUrl}
                    alt={currentUser.username}
                    width={40}
                    height={40}
                    className="rounded-full"
                  />
                ) : (
                  <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {getUserInitials(currentUser)}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {currentUser.displayName || currentUser.username}
                  </p>
                  <p className="text-xs text-gray-500 flex items-center">
                    <span className="mr-1">⭐</span>
                    {currentUser.reputation} reputation
                  </p>
                </div>
                <button
                                onClick={logout}
                                className="flex items-center justify-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                                title="Logout"
                              >
                                <LogOut className="w-4 h-4" />
                              </button>
              </div>
            </Link>

          </>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600 text-center mb-3">
              Login to create posts and interact
            </p>
            <button
              onClick={login}
              className="flex items-center justify-center space-x-2 w-full bg-primary-600 hover:bg-primary-700 text-white font-medium px-4 py-3 rounded-lg transition-colors"
            >
              <LogIn className="w-5 h-5" />
              <span>Login with Google</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
