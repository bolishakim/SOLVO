'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Filter,
  ChevronLeft,
  ChevronRight,
  Globe,
  Monitor,
  Smartphone,
  Tablet,
  CheckCircle,
  XCircle,
  LogOut,
  Download,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PageHeader } from '@/components/layout';
import { useAdminLoginHistory } from '@/services/admin';
import { t } from '@/lib/translations';
import type { LoginHistoryEntry } from '@/types';

function parseUserAgent(userAgent: string): { device: string; browser: string; icon: React.ComponentType<{ className?: string }> } {
  const ua = userAgent.toLowerCase();

  let device = 'Desktop';
  let icon: React.ComponentType<{ className?: string }> = Monitor;

  if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
    device = 'Smartphone';
    icon = Smartphone;
  } else if (ua.includes('tablet') || ua.includes('ipad')) {
    device = 'Tablet';
    icon = Tablet;
  }

  let browser = 'Unbekannt';
  if (ua.includes('firefox')) {
    browser = 'Firefox';
  } else if (ua.includes('edg')) {
    browser = 'Edge';
  } else if (ua.includes('chrome')) {
    browser = 'Chrome';
  } else if (ua.includes('safari')) {
    browser = 'Safari';
  } else if (ua.includes('opera') || ua.includes('opr')) {
    browser = 'Opera';
  }

  return { device, browser, icon };
}

function StatusBadge({ actionType }: { actionType: LoginHistoryEntry['action_type'] }) {
  switch (actionType) {
    case 'LOGIN':
      return (
        <Badge variant="default" className="gap-1">
          <CheckCircle className="h-3 w-3" />
          {t.loginHistory.success}
        </Badge>
      );
    case 'LOGIN_FAILED':
      return (
        <Badge variant="destructive" className="gap-1">
          <XCircle className="h-3 w-3" />
          {t.loginHistory.failed}
        </Badge>
      );
    case 'LOGOUT':
      return (
        <Badge variant="secondary" className="gap-1">
          <LogOut className="h-3 w-3" />
          {t.loginHistory.logout}
        </Badge>
      );
    default:
      return null;
  }
}

function LoginHistoryRow({ entry }: { entry: LoginHistoryEntry }) {
  const { device, browser, icon: DeviceIcon } = parseUserAgent(entry.user_agent);
  const isFailed = entry.action_type === 'LOGIN_FAILED';

  // Get display username - try username, then attempted_username from changes, then fallback
  const displayUsername = entry.username
    || entry.changes?.attempted_username
    || (entry.user_id ? `User #${entry.user_id}` : 'Unbekannt');

  return (
    <TableRow className={isFailed ? 'bg-destructive/5' : ''}>
      <TableCell>
        <div className="space-y-1">
          <p className="font-medium">
            {format(new Date(entry.created_at), 'dd.MM.yyyy', { locale: de })}
          </p>
          <p className="text-xs text-muted-foreground">
            {format(new Date(entry.created_at), 'HH:mm:ss', { locale: de })}
          </p>
        </div>
      </TableCell>
      <TableCell>
        <span className="font-medium">{displayUsername}</span>
      </TableCell>
      <TableCell>
        <StatusBadge actionType={entry.action_type} />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-muted-foreground" />
          <span className="font-mono text-sm">{entry.ip_address}</span>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <DeviceIcon className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-sm">{device}</p>
            <p className="text-xs text-muted-foreground">{browser}</p>
          </div>
        </div>
      </TableCell>
      <TableCell>
        {entry.description && (
          <p className="text-sm text-muted-foreground max-w-[200px] truncate" title={entry.description}>
            {entry.description}
          </p>
        )}
      </TableCell>
    </TableRow>
  );
}

export default function AdminLoginHistoryPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<{
    status?: string;
    from_date?: string;
    to_date?: string;
  }>({});

  const { data: historyData, isLoading } = useAdminLoginHistory({
    page,
    page_size: 20,
    status: filters.status,
    from_date: filters.from_date,
    to_date: filters.to_date,
  });

  const entries = historyData?.data || [];
  const pagination = historyData?.pagination;

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const hasActiveFilters = Object.keys(filters).length > 0;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.admin.loginHistory.title} description={t.admin.loginHistory.subtitle} />
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t.admin.loginHistory.title}
        description={t.admin.loginHistory.subtitle}
      >
        <Button variant="outline" size="sm">
          <Download className="mr-2 h-4 w-4" />
          {t.admin.loginHistory.export}
        </Button>
      </PageHeader>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t.admin.loginHistory.title}</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="mb-4 flex flex-wrap items-end gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
            </div>

            <div className="space-y-1">
              <Label className="text-xs">{t.admin.loginHistory.filters.status}</Label>
              <Select
                value={filters.status || 'all'}
                onValueChange={(value) => {
                  setFilters((prev) => ({
                    ...prev,
                    status: value === 'all' ? undefined : value,
                  }));
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.admin.loginHistory.filters.all}</SelectItem>
                  <SelectItem value="LOGIN">{t.admin.loginHistory.filters.success}</SelectItem>
                  <SelectItem value="LOGIN_FAILED">{t.admin.loginHistory.filters.failed}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label className="text-xs">{t.admin.auditLogs.filters.from}</Label>
              <Input
                type="date"
                className="w-40"
                value={filters.from_date || ''}
                onChange={(e) => {
                  setFilters((prev) => ({
                    ...prev,
                    from_date: e.target.value || undefined,
                  }));
                  setPage(1);
                }}
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs">{t.admin.auditLogs.filters.to}</Label>
              <Input
                type="date"
                className="w-40"
                value={filters.to_date || ''}
                onChange={(e) => {
                  setFilters((prev) => ({
                    ...prev,
                    to_date: e.target.value || undefined,
                  }));
                  setPage(1);
                }}
              />
            </div>

            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                {t.admin.auditLogs.filters.clearFilters}
              </Button>
            )}
          </div>

          {/* Table */}
          {entries.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[100px]">{t.admin.loginHistory.columns.timestamp}</TableHead>
                      <TableHead>{t.admin.loginHistory.columns.user}</TableHead>
                      <TableHead>{t.admin.loginHistory.columns.status}</TableHead>
                      <TableHead>{t.admin.loginHistory.columns.ipAddress}</TableHead>
                      <TableHead>{t.admin.loginHistory.columns.device}</TableHead>
                      <TableHead>{t.admin.loginHistory.columns.details}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entries.map((entry) => (
                      <LoginHistoryRow key={entry.log_id} entry={entry} />
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {pagination && pagination.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Seite {pagination.page} von {pagination.total_pages} ({pagination.total_items} Einträge)
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                      disabled={page === pagination.total_pages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="py-12 text-center text-muted-foreground">
              {t.admin.loginHistory.noHistory}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
