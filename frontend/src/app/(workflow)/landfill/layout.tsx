'use client';

import { useState } from 'react';
import { WorkflowSidebar, Header } from '@/components/layout';
import { useCurrentUser } from '@/services/auth';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
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
  ArrowLeft,
} from 'lucide-react';
import { t } from '@/lib/translations';

// Mobile navigation items
const mobileNavigation = [
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

export default function LandfillLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data: user } = useCurrentUser();
  const pathname = usePathname();

  const isActive = (href: string) => {
    // For dashboard (exact path), only match exactly
    if (href === '/landfill') {
      return pathname === '/landfill';
    }
    return pathname === href || pathname.startsWith(href + '/');
  };

  return (
    <div className="flex h-full">
      {/* Desktop Workflow Sidebar */}
      <aside className="hidden lg:flex">
        <WorkflowSidebar workflowCode="landfill" />
      </aside>

      {/* Mobile Workflow Sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-72 p-0">
          {/* Header */}
          <div className="flex h-16 items-center gap-3 border-b px-4">
            <div className="p-2 rounded-lg bg-emerald-500/10">
              <Truck className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <h2 className="font-semibold text-sm">Deponie</h2>
              <p className="text-xs text-muted-foreground">{t.workflows.title}</p>
            </div>
          </div>

          {/* Back to Dashboard */}
          <div className="border-b px-3 py-2">
            <Link href="/dashboard" onClick={() => setMobileOpen(false)}>
              <Button variant="ghost" size="sm" className="w-full justify-start gap-2 h-9">
                <ArrowLeft className="h-4 w-4" />
                <span className="text-sm">{t.workflows.backToDashboard}</span>
              </Button>
            </Link>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="space-y-1 px-3">
              {mobileNavigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                >
                  <Button
                    variant="ghost"
                    className={cn(
                      'w-full justify-start h-10 gap-3',
                      isActive(item.href) && 'bg-accent text-accent-foreground'
                    )}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.title}</span>
                  </Button>
                </Link>
              ))}
            </nav>
          </ScrollArea>
        </SheetContent>
      </Sheet>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header user={user!} onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto bg-muted/30 p-4 sm:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
