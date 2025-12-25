'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useCurrentUser } from '@/services/auth';
import { isAuthenticated, clearTokens } from '@/lib/api';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Public routes that don't require authentication
const publicRoutes = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-email',
  '/2fa-verify',
];

// Routes that require admin role
const adminRoutes = ['/admin'];

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);

  const { data: user, isLoading, isError } = useCurrentUser();

  const hasRole = (role: string): boolean => {
    if (!user?.roles) return false;
    return user.roles.includes(role);
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!user?.roles) return false;
    return roles.some(role => user.roles.includes(role));
  };

  useEffect(() => {
    const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));
    const isAdminRoute = adminRoutes.some(route => pathname.startsWith(route));
    const hasToken = isAuthenticated();

    // If not loading and ready to make decisions
    if (!isLoading) {
      // If on public route and authenticated, redirect to dashboard
      if (isPublicRoute && hasToken && user) {
        router.replace('/dashboard');
        return;
      }

      // If on protected route and not authenticated
      if (!isPublicRoute && !hasToken) {
        router.replace('/login');
        return;
      }

      // If on protected route, has token but error fetching user (invalid token)
      if (!isPublicRoute && hasToken && isError) {
        clearTokens();
        router.replace('/login');
        return;
      }

      // If on admin route but not admin
      if (isAdminRoute && user && !hasRole('admin')) {
        router.replace('/dashboard');
        return;
      }

      setIsReady(true);
    }
  }, [isLoading, user, isError, pathname, router]);

  // Show nothing while checking auth
  if (!isReady && !publicRoutes.some(route => pathname.startsWith(route))) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user: user || null,
        isLoading,
        isAuthenticated: !!user,
        hasRole,
        hasAnyRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
