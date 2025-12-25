'use client';

import { useState } from 'react';
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
  Truck,
  LayoutDashboard,
  FileText,
  Scale,
  AlertTriangle,
  Building2,
  Briefcase,
  MapPin,
  Boxes,
  Download,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  Home,
} from 'lucide-react';
import { t } from '@/lib/translations';

interface WorkflowNavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

// Landfill workflow navigation
const landfillNavigation: WorkflowNavItem[] = [
  { title: t.nav.dashboard, href: '/landfill', icon: LayoutDashboard },
  { title: t.nav.documents, href: '/landfill/documents', icon: FileText },
  { title: t.nav.weighSlips, href: '/landfill/weigh-slips', icon: Scale },
  { title: t.nav.hazardousSlips, href: '/landfill/hazardous-slips', icon: AlertTriangle },
  { title: t.nav.sites, href: '/landfill/sites', icon: Building2 },
  { title: t.nav.companies, href: '/landfill/companies', icon: Briefcase },
  { title: t.nav.locations, href: '/landfill/locations', icon: MapPin },
  { title: t.nav.materials, href: '/landfill/materials', icon: Boxes },
  { title: t.nav.export, href: '/landfill/export', icon: Download },
];

// Workflow metadata
const WORKFLOW_INFO: Record<string, { title: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
  landfill: {
    title: 'Deponie',
    icon: Truck,
    color: 'text-emerald-600',
  },
};

interface WorkflowSidebarProps {
  workflowCode: string;
}

export function WorkflowSidebar({ workflowCode }: WorkflowSidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const navigation = workflowCode === 'landfill' ? landfillNavigation : [];
  const workflowInfo = WORKFLOW_INFO[workflowCode] || { title: workflowCode, icon: Home, color: 'text-primary' };
  const WorkflowIcon = workflowInfo.icon;

  const isActive = (href: string) => {
    // For dashboard (exact path like /landfill), only match exactly
    if (href === '/landfill') {
      return pathname === '/landfill';
    }
    // For other pages, match path or subpaths
    return pathname === href || pathname.startsWith(href + '/');
  };

  return (
    <div
      className={cn(
        'flex flex-col border-r bg-card transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Workflow Header */}
      <div className={cn(
        'flex h-16 items-center border-b px-4',
        collapsed ? 'justify-center' : 'gap-3'
      )}>
        <div className={cn('p-2 rounded-lg bg-emerald-500/10', collapsed && 'p-1.5')}>
          <WorkflowIcon className={cn('h-5 w-5', workflowInfo.color, collapsed && 'h-4 w-4')} />
        </div>
        {!collapsed && (
          <div className="flex-1 min-w-0">
            <h2 className="font-semibold text-sm truncate">{workflowInfo.title}</h2>
            <p className="text-xs text-muted-foreground">{t.workflows.title}</p>
          </div>
        )}
      </div>

      {/* Back to Dashboard */}
      <div className={cn('border-b', collapsed ? 'px-2 py-2' : 'px-3 py-2')}>
        {collapsed ? (
          <TooltipProvider delayDuration={0}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Link href="/dashboard">
                  <Button variant="ghost" size="icon" className="w-full h-9">
                    <ArrowLeft className="h-4 w-4" />
                  </Button>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right">{t.workflows.backToDashboard}</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ) : (
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="w-full justify-start gap-2 h-9">
              <ArrowLeft className="h-4 w-4" />
              <span className="text-sm">{t.workflows.backToDashboard}</span>
            </Button>
          </Link>
        )}
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 py-4">
        <nav className={cn('space-y-1', collapsed ? 'px-2' : 'px-3')}>
          {navigation.map((item) => {
            const active = isActive(item.href);

            if (collapsed) {
              return (
                <TooltipProvider key={item.href} delayDuration={0}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link href={item.href}>
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
              <Link key={item.href} href={item.href}>
                <Button
                  variant="ghost"
                  className={cn(
                    'w-full justify-start h-10 gap-3',
                    active && 'bg-accent text-accent-foreground'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.title}</span>
                </Button>
              </Link>
            );
          })}
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
