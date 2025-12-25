'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  ArrowLeft,
  User,
  Shield,
  Clock,
  Mail,
  Phone,
  Calendar,
  AlertTriangle,
  Lock,
  Unlock,
  LogOut,
  Key,
  RefreshCw,
  CheckCircle,
  XCircle,
  Plus,
  Trash2,
} from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
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
  useUser,
  useUnlockUser,
  useDeactivateUser,
  useActivateUser,
  useReset2FA,
  useSendPasswordReset,
  useForceLogout,
  useRoles,
  useAssignRole,
  useRemoveRole,
} from '@/services/admin';
import { useAdminLoginHistory } from '@/services/admin';
import { t } from '@/lib/translations';

function InfoRow({ label, value, icon: Icon }: { label: string; value: React.ReactNode; icon?: React.ComponentType<{ className?: string }> }) {
  return (
    <div className="flex items-start gap-3 py-2">
      {Icon && <Icon className="h-4 w-4 mt-0.5 text-muted-foreground" />}
      <div className="flex-1">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="font-medium">{value || '-'}</p>
      </div>
    </div>
  );
}

function StatusBadge({ isActive }: { isActive: boolean }) {
  return isActive ? (
    <Badge variant="default" className="gap-1">
      <CheckCircle className="h-3 w-3" />
      {t.admin.users.badges.active}
    </Badge>
  ) : (
    <Badge variant="secondary" className="gap-1">
      <XCircle className="h-3 w-3" />
      {t.admin.users.badges.inactive}
    </Badge>
  );
}

export default function UserDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params.id as string;
  const [selectedRole, setSelectedRole] = useState<string>('');

  const { data: userData, isLoading } = useUser(userId);
  const { data: roles } = useRoles();
  const { data: loginHistoryData } = useAdminLoginHistory({ user_id: parseInt(userId), page_size: 10 });

  const unlockUser = useUnlockUser();
  const deactivateUser = useDeactivateUser();
  const activateUser = useActivateUser();
  const reset2FA = useReset2FA();
  const sendPasswordReset = useSendPasswordReset();
  const forceLogout = useForceLogout();
  const assignRole = useAssignRole();
  const removeRole = useRemoveRole();

  // API returns user data directly in userData.data, not userData.data.user
  const user = userData?.data;
  const loginHistory = loginHistoryData?.data || [];
  const isLocked = user?.locked_until && new Date(user.locked_until) > new Date();

  // Get roles that can still be assigned (not already assigned)
  const availableRoles = roles?.filter(
    (role) => !user?.roles.includes(role.role_code)
  ) || [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <Skeleton className="h-8 w-48" />
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2">
            <CardContent className="p-6">
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <Skeleton className="h-48 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl font-bold">Benutzer nicht gefunden</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <PageHeader
          title={`${user.first_name} ${user.last_name}`}
          description={t.admin.userDetails.subtitle}
        />
      </div>

      <Tabs defaultValue="info" className="space-y-6">
        <TabsList>
          <TabsTrigger value="info">{t.admin.userDetails.tabs.info}</TabsTrigger>
          <TabsTrigger value="loginHistory">{t.admin.userDetails.tabs.loginHistory}</TabsTrigger>
          <TabsTrigger value="activity">{t.admin.userDetails.tabs.activity}</TabsTrigger>
        </TabsList>

        {/* Info Tab */}
        <TabsContent value="info" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            {/* Personal Information */}
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  {t.admin.userDetails.info.personalInfo}
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <InfoRow label={t.admin.userDetails.info.username} value={user.username} icon={User} />
                <InfoRow label={t.admin.userDetails.info.email} value={user.email} icon={Mail} />
                <InfoRow label={t.admin.userDetails.info.firstName} value={user.first_name} />
                <InfoRow label={t.admin.userDetails.info.lastName} value={user.last_name} />
                <InfoRow label={t.admin.userDetails.info.phoneNumber} value={user.phone_number} icon={Phone} />
                <InfoRow
                  label={t.admin.userDetails.info.createdAt}
                  value={format(new Date(user.created_at), 'dd. MMMM yyyy, HH:mm', { locale: de })}
                  icon={Calendar}
                />
              </CardContent>
            </Card>

            {/* Account Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  {t.admin.userDetails.info.accountInfo}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Status</span>
                  <StatusBadge isActive={user.is_active} />
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">E-Mail</span>
                  {user.is_verified ? (
                    <Badge variant="default" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      {t.profile.verified}
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="gap-1">
                      <XCircle className="h-3 w-3" />
                      {t.profile.notVerified}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">2FA</span>
                  {user.two_factor_enabled ? (
                    <Badge variant="default" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      {t.security.twoFactorEnabled}
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1">
                      <XCircle className="h-3 w-3" />
                      {t.security.twoFactorDisabled}
                    </Badge>
                  )}
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">{t.admin.userDetails.info.lastLogin}:</span>
                  </div>
                  <p className="text-sm font-medium pl-6">
                    {user.last_login_at
                      ? format(new Date(user.last_login_at), 'dd. MMMM yyyy, HH:mm', { locale: de })
                      : '-'}
                  </p>
                </div>

                {isLocked && (
                  <>
                    <Separator />
                    <div className="rounded-md bg-destructive/10 p-3">
                      <div className="flex items-center gap-2 text-destructive">
                        <Lock className="h-4 w-4" />
                        <span className="font-medium">{t.admin.users.badges.locked}</span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {t.admin.userDetails.info.lockedUntil}: {format(new Date(user.locked_until!), 'dd.MM.yyyy HH:mm', { locale: de })}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {t.admin.userDetails.info.failedAttempts}: {user.failed_login_attempts}
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-2"
                        onClick={() => unlockUser.mutate(userId)}
                        disabled={unlockUser.isPending}
                      >
                        <Unlock className="mr-2 h-4 w-4" />
                        {t.admin.users.actions.unlock}
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Roles Section */}
          <Card>
            <CardHeader>
              <CardTitle>{t.admin.userDetails.roles.title}</CardTitle>
              <CardDescription>{t.admin.userDetails.roles.subtitle}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 mb-4">
                {user.roles.length > 0 ? (
                  user.roles.map((roleCode) => {
                    const role = roles?.find((r) => r.role_code === roleCode);
                    return (
                      <Badge key={roleCode} variant="secondary" className="gap-2 py-1.5 px-3">
                        {role?.role_name || roleCode}
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-4 w-4 p-0 hover:bg-transparent">
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>{t.admin.userDetails.roles.confirmRemove}</AlertDialogTitle>
                              <AlertDialogDescription>
                                {t.admin.userDetails.roles.confirmRemoveDescription}
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => removeRole.mutate({ userId, roleCode })}
                              >
                                {t.admin.userDetails.roles.removeRole}
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </Badge>
                    );
                  })
                ) : (
                  <p className="text-sm text-muted-foreground">{t.admin.userDetails.roles.noRoles}</p>
                )}
              </div>

              {availableRoles.length > 0 && (
                <div className="flex items-center gap-2">
                  <Select value={selectedRole} onValueChange={setSelectedRole}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder={t.admin.userDetails.roles.assignRole} />
                    </SelectTrigger>
                    <SelectContent>
                      {availableRoles.map((role) => (
                        <SelectItem key={role.role_code} value={role.role_code}>
                          {role.role_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    size="sm"
                    disabled={!selectedRole || assignRole.isPending}
                    onClick={() => {
                      if (selectedRole) {
                        assignRole.mutate({ userId, roleCode: selectedRole });
                        setSelectedRole('');
                      }
                    }}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    {t.admin.userDetails.roles.assignRole}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Security Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                {t.admin.userDetails.securityActions.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {/* Force Logout */}
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" className="justify-start">
                      <LogOut className="mr-2 h-4 w-4" />
                      {t.admin.userDetails.securityActions.forceLogout}
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>{t.admin.userDetails.securityActions.confirmAction}</AlertDialogTitle>
                      <AlertDialogDescription>
                        {t.admin.userDetails.securityActions.forceLogoutDescription}
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
                      <AlertDialogAction onClick={() => forceLogout.mutate(userId)}>
                        {t.admin.userDetails.securityActions.forceLogout}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>

                {/* Reset 2FA */}
                {user.two_factor_enabled && (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" className="justify-start">
                        <RefreshCw className="mr-2 h-4 w-4" />
                        {t.admin.userDetails.securityActions.reset2FA}
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>{t.admin.userDetails.securityActions.confirmAction}</AlertDialogTitle>
                        <AlertDialogDescription>
                          {t.admin.userDetails.securityActions.reset2FADescription}
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
                        <AlertDialogAction onClick={() => reset2FA.mutate(userId)}>
                          {t.admin.userDetails.securityActions.reset2FA}
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                )}

                {/* Send Password Reset */}
                <Button
                  variant="outline"
                  className="justify-start"
                  onClick={() => sendPasswordReset.mutate(userId)}
                  disabled={sendPasswordReset.isPending}
                >
                  <Key className="mr-2 h-4 w-4" />
                  {t.admin.userDetails.securityActions.sendPasswordReset}
                </Button>

                {/* Activate/Deactivate */}
                {user.is_active ? (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="destructive" className="justify-start">
                        <XCircle className="mr-2 h-4 w-4" />
                        {t.admin.users.actions.deactivate}
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>{t.admin.userDetails.securityActions.confirmAction}</AlertDialogTitle>
                        <AlertDialogDescription>
                          Dieser Benutzer wird deaktiviert und kann sich nicht mehr anmelden.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
                        <AlertDialogAction onClick={() => deactivateUser.mutate(userId)}>
                          {t.admin.users.actions.deactivate}
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                ) : (
                  <Button
                    variant="default"
                    className="justify-start"
                    onClick={() => activateUser.mutate(userId)}
                    disabled={activateUser.isPending}
                  >
                    <CheckCircle className="mr-2 h-4 w-4" />
                    {t.admin.users.actions.activate}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Login History Tab */}
        <TabsContent value="loginHistory">
          <Card>
            <CardHeader>
              <CardTitle>{t.admin.userDetails.tabs.loginHistory}</CardTitle>
            </CardHeader>
            <CardContent>
              {loginHistory.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t.loginHistory.date}</TableHead>
                        <TableHead>{t.loginHistory.status}</TableHead>
                        <TableHead>{t.loginHistory.ipAddress}</TableHead>
                        <TableHead>{t.common.details}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {loginHistory.map((entry) => (
                        <TableRow key={entry.log_id} className={entry.action_type === 'LOGIN_FAILED' ? 'bg-destructive/5' : ''}>
                          <TableCell>
                            {format(new Date(entry.created_at), 'dd.MM.yyyy HH:mm', { locale: de })}
                          </TableCell>
                          <TableCell>
                            {entry.action_type === 'LOGIN' && (
                              <Badge variant="default" className="gap-1">
                                <CheckCircle className="h-3 w-3" />
                                {t.loginHistory.success}
                              </Badge>
                            )}
                            {entry.action_type === 'LOGIN_FAILED' && (
                              <Badge variant="destructive" className="gap-1">
                                <XCircle className="h-3 w-3" />
                                {t.loginHistory.failed}
                              </Badge>
                            )}
                            {entry.action_type === 'LOGOUT' && (
                              <Badge variant="secondary">{t.loginHistory.logout}</Badge>
                            )}
                          </TableCell>
                          <TableCell className="font-mono text-sm">{entry.ip_address}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {entry.description || '-'}
                          </TableCell>
                        </TableRow>
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
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle>{t.admin.userDetails.tabs.activity}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="py-12 text-center text-muted-foreground">
                {t.common.comingSoon}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
