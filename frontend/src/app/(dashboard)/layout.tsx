'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar, Header, MobileSidebar } from '@/components/layout';
import { useCurrentUser } from '@/services/auth';
import { isAuthenticated } from '@/lib/api';
import { Loader2 } from 'lucide-react';
import { t } from '@/lib/translations';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
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

  const isAdmin = user.roles?.some(role =>
    role.toLowerCase() === 'admin' || role === 'Admin' || role === 'Administrator'
  ) ?? false;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex">
        <Sidebar isAdmin={isAdmin} />
      </aside>

      {/* Mobile Sidebar */}
      <MobileSidebar
        open={mobileOpen}
        onOpenChange={setMobileOpen}
        isAdmin={isAdmin}
      />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header user={user} onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto bg-muted/30 p-4 sm:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
