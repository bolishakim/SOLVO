'use client';

import { Fragment } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { t } from '@/lib/translations';

const routeLabels: Record<string, string> = {
  dashboard: t.breadcrumbs.dashboard,
  profile: t.breadcrumbs.profile,
  security: t.breadcrumbs.security,
  sessions: t.breadcrumbs.sessions,
  'login-history': t.breadcrumbs.loginHistory,
  admin: t.breadcrumbs.admin,
  users: t.breadcrumbs.users,
  roles: t.breadcrumbs.roles,
  'audit-logs': t.breadcrumbs.auditLogs,
  stats: t.breadcrumbs.stats,
  landfill: t.breadcrumbs.landfill,
  documents: t.breadcrumbs.documents,
  'weigh-slips': t.breadcrumbs.weighSlips,
  'hazardous-slips': t.breadcrumbs.hazardousSlips,
  sites: t.breadcrumbs.sites,
  companies: t.breadcrumbs.companies,
  locations: t.breadcrumbs.locations,
  materials: t.breadcrumbs.materials,
  export: t.breadcrumbs.export,
  new: t.breadcrumbs.new,
  edit: t.breadcrumbs.edit,
  upload: t.breadcrumbs.upload,
};

export function Breadcrumbs() {
  const pathname = usePathname();

  // Split pathname and filter empty strings
  const segments = pathname.split('/').filter(Boolean);

  // Build breadcrumb items
  const breadcrumbs = segments.map((segment, index) => {
    const href = '/' + segments.slice(0, index + 1).join('/');
    const label = routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
    const isLast = index === segments.length - 1;

    // Check if segment is a dynamic ID (UUID or number)
    const isDynamicId = /^[0-9a-f-]{36}$|^\d+$/.test(segment);

    return {
      href,
      label: isDynamicId ? t.breadcrumbs.details : label,
      isLast,
    };
  });

  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center text-sm">
      <ol className="flex items-center gap-1">
        <li>
          <Link
            href="/dashboard"
            className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <Home className="h-4 w-4" />
          </Link>
        </li>
        {breadcrumbs.map((crumb, index) => (
          <Fragment key={crumb.href}>
            <li>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </li>
            <li>
              {crumb.isLast ? (
                <span className="font-medium text-foreground">
                  {crumb.label}
                </span>
              ) : (
                <Link
                  href={crumb.href}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  {crumb.label}
                </Link>
              )}
            </li>
          </Fragment>
        ))}
      </ol>
    </nav>
  );
}
