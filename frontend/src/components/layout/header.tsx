'use client';

import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Breadcrumbs } from './breadcrumbs';
import { UserMenu } from './user-menu';
import { ThemeToggle } from '@/components/theme-toggle';
import type { User } from '@/types';

interface HeaderProps {
  user: User;
  onMenuClick?: () => void;
}

export function Header({ user, onMenuClick }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-background px-4 sm:px-6 shadow-nav">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
      >
        <Menu className="h-5 w-5" />
        <span className="sr-only">Toggle menu</span>
      </Button>

      {/* Breadcrumbs */}
      <div className="flex-1">
        <Breadcrumbs />
      </div>

      {/* Right side actions */}
      <div className="flex items-center gap-2">
        <ThemeToggle />
        <UserMenu user={user} />
      </div>
    </header>
  );
}
