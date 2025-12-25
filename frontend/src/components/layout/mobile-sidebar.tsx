'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
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
  FileUp,
  Scale,
  AlertTriangle,
  Building2,
  MapPin,
  Boxes,
  Download,
  ChevronDown,
} from 'lucide-react';
import { t } from '@/lib/translations';

// Use same localStorage key as main sidebar for consistency
const SIDEBAR_EXPANDED_ITEMS_KEY = 'sidebar-expanded-items';

interface NavItem {
  title: string;
  href?: string;
  icon: React.ComponentType<{ className?: string }>;
  children?: NavItem[];
  adminOnly?: boolean;
}

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
  {
    title: t.nav.landfill,
    icon: Recycle,
    children: [
      { title: t.nav.documents, href: '/landfill/documents', icon: FileUp },
      { title: t.nav.weighSlips, href: '/landfill/weigh-slips', icon: Scale },
      { title: t.nav.hazardousSlips, href: '/landfill/hazardous-slips', icon: AlertTriangle },
      { title: t.nav.sites, href: '/landfill/sites', icon: Building2 },
      { title: t.nav.companies, href: '/landfill/companies', icon: Building2 },
      { title: t.nav.locations, href: '/landfill/locations', icon: MapPin },
      { title: t.nav.materials, href: '/landfill/materials', icon: Boxes },
      { title: t.nav.export, href: '/landfill/export', icon: Download },
    ],
  },
];

interface MobileSidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  isAdmin?: boolean;
}

export function MobileSidebar({ open, onOpenChange, isAdmin = false }: MobileSidebarProps) {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  // Load state from localStorage on mount
  useEffect(() => {
    setMounted(true);
    try {
      const savedExpanded = localStorage.getItem(SIDEBAR_EXPANDED_ITEMS_KEY);
      if (savedExpanded !== null) {
        setExpandedItems(JSON.parse(savedExpanded));
      }
    } catch (e) {
      // Ignore localStorage errors
    }
  }, []);

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

  const handleLinkClick = () => {
    onOpenChange(false);
  };

  const renderNavItem = (item: NavItem, depth = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.title);
    const active = isParentActive(item);

    if (hasChildren) {
      const filteredChildren = item.children!.filter(
        (child) => !child.adminOnly || isAdmin
      );

      return (
        <div key={item.title}>
          <Button
            variant="ghost"
            className={cn(
              'w-full justify-between h-11',
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

    return (
      <Link key={item.href} href={item.href!} onClick={handleLinkClick}>
        <Button
          variant="ghost"
          className={cn(
            'w-full justify-start h-11 gap-3',
            active && 'bg-accent text-accent-foreground',
            depth > 0 && 'h-10 text-sm'
          )}
        >
          <item.icon className={cn('h-5 w-5', depth > 0 && 'h-4 w-4')} />
          <span>{item.title}</span>
        </Button>
      </Link>
    );
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-72 p-0 shadow-nav-lg">
        <SheetHeader className="h-16 border-b px-4 flex flex-row items-center gap-3">
          <Recycle className="h-7 w-7 text-primary" />
          <SheetTitle className="text-left font-bold text-xl tracking-wide text-primary">{t.app.name}</SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-4rem)]">
          <nav className="space-y-1 p-3">
            {filteredNavigation.map((item) => renderNavItem(item))}
          </nav>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
