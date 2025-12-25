'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Recycle,
  LayoutDashboard,
  User,
  Settings,
  Shield,
  Monitor,
  History,
  Users,
  UserCog,
  FileText,
  BarChart3,
  Lock,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
} from 'lucide-react';
import { t } from '@/lib/translations';

// LocalStorage keys
const SIDEBAR_COLLAPSED_KEY = 'sidebar-collapsed';
const SIDEBAR_EXPANDED_ITEMS_KEY = 'sidebar-expanded-items';

interface NavItem {
  title: string;
  href?: string;
  icon: React.ComponentType<{ className?: string }>;
  children?: NavItem[];
  adminOnly?: boolean;
}

// Main navigation (without workflow-specific items - those are in workflow sidebar)
const navigation: NavItem[] = [
  {
    title: t.nav.workflows,
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: t.nav.profile,
    icon: User,
    children: [
      { title: t.nav.settings, href: '/profile', icon: Settings },
      { title: t.nav.security, href: '/profile/security', icon: Shield },
      { title: t.nav.sessions, href: '/profile/sessions', icon: Monitor },
      { title: t.nav.loginHistory, href: '/profile/login-history', icon: History },
    ],
  },
  {
    title: t.nav.admin,
    icon: UserCog,
    adminOnly: true,
    children: [
      { title: t.nav.users, href: '/admin/users', icon: Users },
      { title: t.nav.roles, href: '/admin/roles', icon: UserCog },
      { title: t.nav.auditLogs, href: '/admin/audit-logs', icon: FileText },
      { title: t.nav.loginHistory, href: '/admin/login-history', icon: History },
      { title: t.nav.security, href: '/admin/security', icon: Lock },
      { title: t.nav.statistics, href: '/admin/stats', icon: BarChart3 },
    ],
  },
];

interface SidebarProps {
  isAdmin?: boolean;
}

export function Sidebar({ isAdmin = false }: SidebarProps) {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  // Load state from localStorage on mount
  useEffect(() => {
    setMounted(true);
    try {
      const savedCollapsed = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      if (savedCollapsed !== null) {
        setCollapsed(JSON.parse(savedCollapsed));
      }
      const savedExpanded = localStorage.getItem(SIDEBAR_EXPANDED_ITEMS_KEY);
      if (savedExpanded !== null) {
        setExpandedItems(JSON.parse(savedExpanded));
      }
    } catch (e) {
      // Ignore localStorage errors
    }
  }, []);

  // Persist collapsed state to localStorage
  useEffect(() => {
    if (mounted) {
      try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, JSON.stringify(collapsed));
      } catch (e) {
        // Ignore localStorage errors
      }
    }
  }, [collapsed, mounted]);

  // Persist expanded items to localStorage
  useEffect(() => {
    if (mounted) {
      try {
        localStorage.setItem(SIDEBAR_EXPANDED_ITEMS_KEY, JSON.stringify(expandedItems));
      } catch (e) {
        // Ignore localStorage errors
      }
    }
  }, [expandedItems, mounted]);

  const toggleExpanded = (title: string) => {
    setExpandedItems((prev) =>
      prev.includes(title)
        ? prev.filter((item) => item !== title)
        : [...prev, title]
    );
  };

  const isActive = (href?: string) => {
    if (!href) return false;
    return pathname === href || pathname.startsWith(href + '/');
  };

  const isParentActive = (item: NavItem) => {
    if (item.href) return isActive(item.href);
    return item.children?.some((child) => isActive(child.href)) ?? false;
  };

  const filteredNavigation = navigation.filter(
    (item) => !item.adminOnly || isAdmin
  );

  const renderNavItem = (item: NavItem, depth = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.title);
    const active = isParentActive(item);

    if (hasChildren) {
      const filteredChildren = item.children!.filter(
        (child) => !child.adminOnly || isAdmin
      );

      if (collapsed) {
        return (
          <TooltipProvider key={item.title} delayDuration={0}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    'w-full h-10 justify-center',
                    active && 'bg-accent text-accent-foreground'
                  )}
                  onClick={() => setCollapsed(false)}
                >
                  <item.icon className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right" className="flex flex-col gap-1">
                <span className="font-medium">{item.title}</span>
                {filteredChildren.map((child) => (
                  <Link
                    key={child.href}
                    href={child.href!}
                    className={cn(
                      'text-sm hover:underline',
                      isActive(child.href) && 'font-medium'
                    )}
                  >
                    {child.title}
                  </Link>
                ))}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );
      }

      return (
        <div key={item.title}>
          <Button
            variant="ghost"
            className={cn(
              'w-full justify-between h-10',
              active && 'bg-accent text-accent-foreground'
            )}
            onClick={() => toggleExpanded(item.title)}
          >
            <span className="flex items-center gap-3">
              <item.icon className="h-5 w-5" />
              <span>{item.title}</span>
            </span>
            <ChevronDown
              className={cn(
                'h-4 w-4 transition-transform',
                isExpanded && 'rotate-180'
              )}
            />
          </Button>
          {isExpanded && (
            <div className="ml-4 mt-1 space-y-1 border-l pl-4">
              {filteredChildren.map((child) => renderNavItem(child, depth + 1))}
            </div>
          )}
        </div>
      );
    }

    if (collapsed) {
      return (
        <TooltipProvider key={item.href} delayDuration={0}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Link href={item.href!}>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    'w-full h-10 justify-center',
                    active && 'bg-accent text-accent-foreground'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">{item.title}</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    return (
      <Link key={item.href} href={item.href!}>
        <Button
          variant="ghost"
          className={cn(
            'w-full justify-start h-10 gap-3',
            active && 'bg-accent text-accent-foreground',
            depth > 0 && 'h-9 text-sm'
          )}
        >
          <item.icon className={cn('h-5 w-5', depth > 0 && 'h-4 w-4')} />
          <span>{item.title}</span>
        </Button>
      </Link>
    );
  };

  return (
    <div
      className={cn(
        'flex flex-col border-r bg-card transition-all duration-300 shadow-nav',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className={cn(
        'flex h-16 items-center border-b px-4',
        collapsed ? 'justify-center' : 'gap-3'
      )}>
        <Recycle className="h-7 w-7 text-primary flex-shrink-0" />
        {!collapsed && (
          <span className="font-bold text-xl tracking-wide text-primary">{t.app.name}</span>
        )}
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 py-4">
        <nav className={cn('space-y-1', collapsed ? 'px-2' : 'px-3')}>
          {filteredNavigation.map((item) => renderNavItem(item))}
        </nav>
      </ScrollArea>

      {/* Collapse Toggle */}
      <div className="border-t p-2">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-center"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span>{t.nav.collapse}</span>
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
