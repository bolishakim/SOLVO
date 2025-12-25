'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  CheckCircle,
  XCircle,
  LogOut,
  AlertTriangle,
  Filter,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
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
import { useLoginHistory } from '@/services/profile';
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

export default function LoginHistoryPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: historyData, isLoading } = useLoginHistory({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    limit: 50,
  });

  const entries = historyData?.data || [];
  const failedCount = entries.filter(e => e.action_type === 'LOGIN_FAILED').length;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.loginHistory.title} description={t.loginHistory.subtitle} />
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              <Skeleton className="h-10 w-48" />
              <Skeleton className="h-64 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.loginHistory.title} description={t.loginHistory.subtitle} />

      {/* Warning for failed logins */}
      {failedCount > 3 && (
        <Card className="border-amber-500 bg-amber-50 dark:bg-amber-950/20">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800 dark:text-amber-200">
                {t.loginHistory.suspiciousActivity}
              </p>
              <p className="text-sm text-amber-700 dark:text-amber-300">
                {failedCount} fehlgeschlagene Anmeldeversuche in den letzten Einträgen.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{t.loginHistory.title}</CardTitle>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t.loginHistory.filterByStatus} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.loginHistory.all}</SelectItem>
                  <SelectItem value="LOGIN">{t.loginHistory.successOnly}</SelectItem>
                  <SelectItem value="LOGIN_FAILED">{t.loginHistory.failedOnly}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {entries.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">{t.loginHistory.date}</TableHead>
                    <TableHead className="w-[120px]">{t.loginHistory.status}</TableHead>
                    <TableHead className="w-[150px]">{t.loginHistory.ipAddress}</TableHead>
                    <TableHead className="w-[180px]">{t.loginHistory.device}</TableHead>
                    <TableHead>{t.common.details}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((entry) => (
                    <LoginHistoryRow key={entry.log_id} entry={entry} />
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-12 text-center text-muted-foreground">
              {t.loginHistory.noHistory}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
