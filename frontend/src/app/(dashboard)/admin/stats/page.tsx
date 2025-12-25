'use client';

import {
  Users,
  UserCheck,
  Shield,
  Activity,
  Clock,
  FileText,
  LogIn,
  XCircle,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader } from '@/components/layout';
import { useAuditStats, useSecurityStats } from '@/services/admin';
import { t } from '@/lib/translations';

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            )}
          </div>
          <Icon className="h-8 w-8 text-muted-foreground opacity-80" />
        </div>
      </CardContent>
    </Card>
  );
}

function ActivityBreakdown({
  title,
  data,
  getLabel,
}: {
  title: string;
  data: Record<string, number> | undefined;
  getLabel: (key: string) => string;
}) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{t.admin.statistics.noData}</p>
        </CardContent>
      </Card>
    );
  }

  const sortedEntries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const total = sortedEntries.reduce((sum, [, count]) => sum + count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedEntries.slice(0, 8).map(([key, count]) => {
            const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
            return (
              <div key={key} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span>{getLabel(key)}</span>
                  <span className="text-muted-foreground">{count} ({percentage}%)</span>
                </div>
                <div className="h-2 rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default function StatsPage() {
  const { data: auditStats, isLoading: auditLoading } = useAuditStats();
  const { data: securityStats, isLoading: securityLoading } = useSecurityStats();

  const isLoading = auditLoading || securityLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.admin.statistics.title} description={t.admin.statistics.subtitle} />
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.admin.statistics.title} description={t.admin.statistics.subtitle} />

      {/* User Stats */}
      <div>
        <h3 className="text-lg font-medium mb-4">{t.admin.statistics.userStats.title}</h3>
        <div className="grid gap-4 md:grid-cols-4">
          <StatCard
            title={t.admin.statistics.userStats.totalUsers}
            value={securityStats?.total_users || 0}
            icon={Users}
          />
          <StatCard
            title={t.admin.statistics.userStats.activeUsers}
            value={securityStats?.active_users || 0}
            icon={UserCheck}
          />
          <StatCard
            title={t.admin.statistics.userStats.verifiedUsers}
            value={(securityStats?.total_users || 0) - (securityStats?.unverified_users || 0)}
            icon={UserCheck}
          />
          <StatCard
            title={t.admin.statistics.userStats.usersWithTwoFactor}
            value={`${securityStats?.two_factor_adoption_rate || 0}%`}
            icon={Shield}
          />
        </div>
      </div>

      {/* Activity Stats */}
      <div>
        <h3 className="text-lg font-medium mb-4">{t.admin.statistics.activityStats.title}</h3>
        <div className="grid gap-4 md:grid-cols-4">
          <StatCard
            title={t.admin.statistics.activityStats.totalLogins}
            value={auditStats?.total_logs || 0}
            icon={LogIn}
          />
          <StatCard
            title={t.admin.statistics.activityStats.loginsToday}
            value={auditStats?.recent_24h || 0}
            subtitle={t.admin.statistics.auditStats.logsLast24h}
            icon={Activity}
          />
          <StatCard
            title={t.admin.statistics.activityStats.failedLoginsToday}
            value={auditStats?.failed_logins_24h || securityStats?.failed_logins_24h || 0}
            icon={XCircle}
          />
          <StatCard
            title={t.admin.statistics.activityStats.activeSessionsNow}
            value={0}
            icon={Clock}
          />
        </div>
      </div>

      {/* Audit Stats */}
      <div>
        <h3 className="text-lg font-medium mb-4">{t.admin.statistics.auditStats.title}</h3>
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          <StatCard
            title={t.admin.statistics.auditStats.totalLogs}
            value={auditStats?.total_logs || 0}
            icon={FileText}
          />
          <StatCard
            title={t.admin.statistics.auditStats.logsLast24h}
            value={auditStats?.recent_24h || 0}
            icon={Activity}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <ActivityBreakdown
            title={t.admin.statistics.auditStats.byAction}
            data={auditStats?.by_action_type}
            getLabel={(key) => t.admin.auditLogs.actions[key as keyof typeof t.admin.auditLogs.actions] || key}
          />
          <ActivityBreakdown
            title={t.admin.statistics.auditStats.byEntity}
            data={auditStats?.by_entity_type}
            getLabel={(key) => t.admin.auditLogs.entities[key as keyof typeof t.admin.auditLogs.entities] || key}
          />
        </div>
      </div>
    </div>
  );
}
