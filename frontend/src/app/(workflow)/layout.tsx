'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCurrentUser } from '@/services/auth';
import { isAuthenticated } from '@/lib/api';
import { Loader2 } from 'lucide-react';
import { t } from '@/lib/translations';

/**
 * Workflow Layout
 *
 * This layout provides authentication checking for workflow pages
 * but does NOT include the main sidebar - each workflow provides its own.
 */
export default function WorkflowLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const { data: user, isLoading, isError, isFetched } = useCurrentUser();

  // Wait for client-side mount before checking auth
  useEffect(() => {
    setMounted(true);
  }, []);

  // Check authentication only after mounting (client-side only)
  // If no token exists, redirect immediately
  useEffect(() => {
    if (mounted && !isAuthenticated()) {
      router.replace('/login');
    }
  }, [mounted, router]);

  // Handle auth errors - only redirect after query has actually been attempted
  useEffect(() => {
    if (mounted && isFetched && !isLoading && isError) {
      router.replace('/login');
    }
  }, [mounted, isFetched, isLoading, isError, router]);

  // Show loading until mounted
  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">{t.common.loading}</p>
        </div>
      </div>
    );
  }

  // If not authenticated, show loading (redirect will happen)
  if (!isAuthenticated()) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">{t.common.loading}</p>
        </div>
      </div>
    );
  }

  // Show loading while fetching user data
  if (isLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">{t.common.loading}</p>
        </div>
      </div>
    );
  }

  // Just render children - each workflow has its own layout with sidebar
  return (
    <div className="h-screen overflow-hidden">
      {children}
    </div>
  );
}
