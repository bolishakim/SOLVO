'use client';

import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Shield,
  Lock,
  AlertTriangle,
  Users,
  CheckCircle,
  XCircle,
  Unlock,
  ArrowRight,
} from 'lucide-react';
import Link from 'next/link';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PageHeader } from '@/components/layout';
import {
  useSecurityStats,
  useLockedAccounts,
  useFailedLogins,
  useUnlockUser,
} from '@/services/admin';
import { t } from '@/lib/translations';

function StatCard({
  title,
  value,
  icon: Icon,
  variant = 'default',
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'warning' | 'danger' | 'success';
}) {
  const colorClasses = {
    default: 'text-primary',
    warning: 'text-amber-600',
    danger: 'text-destructive',
    success: 'text-green-600',
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className={`text-3xl font-bold ${colorClasses[variant]}`}>{value}</p>
          </div>
          <Icon className={`h-8 w-8 ${colorClasses[variant]} opacity-80`} />
        </div>
      </CardContent>
    </Card>
  );
}

export default function AdminSecurityPage() {
  const { data: stats, isLoading: statsLoading } = useSecurityStats();
  const { data: lockedAccounts, isLoading: lockedLoading } = useLockedAccounts();
  const { data: failedLogins, isLoading: failedLoading } = useFailedLogins(24);
  const unlockUser = useUnlockUser();

  const isLoading = statsLoading || lockedLoading || failedLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.admin.security.title} description={t.admin.security.subtitle} />
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  // Group failed logins by user to identify repeat offenders
  const failedByUser: Record<string, number> = {};
  failedLogins?.forEach((login) => {
    const key = login.username || `User #${login.user_id}`;
    failedByUser[key] = (failedByUser[key] || 0) + 1;
  });

  return (
    <div className="space-y-6">
      <PageHeader title={t.admin.security.title} description={t.admin.security.subtitle} />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title={t.admin.security.stats.failedLogins24h}
          value={stats?.failed_logins_24h || 0}
          icon={XCircle}
          variant={stats?.failed_logins_24h && stats.failed_logins_24h > 10 ? 'danger' : 'default'}
        />
        <StatCard
          title={t.admin.security.stats.lockedAccounts}
          value={stats?.locked_accounts || 0}
          icon={Lock}
          variant={stats?.locked_accounts && stats.locked_accounts > 0 ? 'warning' : 'default'}
        />
        <StatCard
          title={t.admin.security.stats.twoFactorAdoption}
          value={`${stats?.two_factor_adoption_rate || 0}%`}
          icon={Shield}
          variant={stats?.two_factor_adoption_rate && stats.two_factor_adoption_rate > 50 ? 'success' : 'warning'}
        />
        <StatCard
          title={t.admin.security.stats.suspiciousActivities}
          value={stats?.suspicious_activities || 0}
          icon={AlertTriangle}
          variant={stats?.suspicious_activities && stats.suspicious_activities > 0 ? 'danger' : 'default'}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Locked Accounts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              {t.admin.security.lockedAccounts.title}
            </CardTitle>
            <CardDescription>{t.admin.security.lockedAccounts.subtitle}</CardDescription>
          </CardHeader>
          <CardContent>
            {lockedAccounts && lockedAccounts.length > 0 ? (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.admin.security.lockedAccounts.columns.user}</TableHead>
                      <TableHead>{t.admin.security.lockedAccounts.columns.unlockTime}</TableHead>
                      <TableHead>{t.admin.security.lockedAccounts.columns.failedAttempts}</TableHead>
                      <TableHead className="w-24">{t.admin.security.lockedAccounts.columns.actions}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {lockedAccounts.map((account) => (
                      <TableRow key={account.user_id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{account.username}</p>
                            <p className="text-sm text-muted-foreground">{account.email}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          {format(new Date(account.locked_until), 'dd.MM.yyyy HH:mm', { locale: de })}
                        </TableCell>
                        <TableCell>
                          <Badge variant="destructive">{account.failed_login_attempts}</Badge>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => unlockUser.mutate(account.user_id.toString())}
                            disabled={unlockUser.isPending}
                          >
                            <Unlock className="mr-1 h-3 w-3" />
                            {t.admin.security.lockedAccounts.unlock}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                <CheckCircle className="mx-auto mb-2 h-8 w-8 text-green-500" />
                <p>{t.admin.security.lockedAccounts.noLocked}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Failed Logins */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              {t.admin.security.failedLogins.title}
            </CardTitle>
            <CardDescription>{t.admin.security.failedLogins.subtitle}</CardDescription>
          </CardHeader>
          <CardContent>
            {failedLogins && failedLogins.length > 0 ? (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.admin.loginHistory.columns.timestamp}</TableHead>
                      <TableHead>{t.admin.loginHistory.columns.user}</TableHead>
                      <TableHead>{t.admin.loginHistory.columns.ipAddress}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {failedLogins.slice(0, 10).map((login) => {
                      const username = login.username || `User #${login.user_id}`;
                      const isRepeatOffender = failedByUser[username] >= 3;

                      return (
                        <TableRow key={login.log_id}>
                          <TableCell>
                            {format(new Date(login.created_at), 'dd.MM. HH:mm', { locale: de })}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{username}</span>
                              {isRepeatOffender && (
                                <Badge variant="destructive" className="text-xs">
                                  {t.admin.security.failedLogins.repeatOffender}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="font-mono text-sm">{login.ip_address}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                <CheckCircle className="mx-auto mb-2 h-8 w-8 text-green-500" />
                <p>{t.admin.security.failedLogins.noFailed}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Security Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            {t.admin.security.recommendations.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {/* Users without 2FA */}
            <div className="rounded-lg border p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium">{t.admin.security.recommendations.usersWithout2FA}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {t.admin.security.recommendations.usersWithout2FADescription(stats?.users_without_2fa || 0)}
                  </p>
                </div>
                <Users className="h-8 w-8 text-amber-500" />
              </div>
              <Button variant="outline" size="sm" className="mt-3" asChild>
                <Link href="/admin/users?two_factor_enabled=false">
                  {t.admin.security.recommendations.viewUsers}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </div>

            {/* Inactive Accounts */}
            <div className="rounded-lg border p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium">{t.admin.security.recommendations.inactiveAccounts}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {t.admin.security.recommendations.inactiveAccountsDescription(stats?.inactive_accounts || 0)}
                  </p>
                </div>
                <AlertTriangle className="h-8 w-8 text-amber-500" />
              </div>
              <Button variant="outline" size="sm" className="mt-3" asChild>
                <Link href="/admin/users">
                  {t.admin.security.recommendations.viewUsers}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
