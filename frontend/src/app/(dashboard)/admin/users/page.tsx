'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Edit,
  Unlock,
  UserX,
  UserCheck,
  CheckCircle,
  XCircle,
  Lock,
  Shield,
  ShieldOff,
  Key,
  ChevronLeft,
  ChevronRight,
  UserPlus,
  Loader2,
  Check,
  X,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/layout';
import { useUsers, useUnlockUser, useDeactivateUser, useActivateUser, useRoles, useCreateUser, useReset2FA, useResetPassword } from '@/services/admin';
import { t } from '@/lib/translations';
import type { AdminUser, Role } from '@/types';

// Form validation schema
const createUserSchema = z.object({
  username: z
    .string()
    .min(3, 'Mindestens 3 Zeichen')
    .max(50, 'Maximal 50 Zeichen')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Nur Buchstaben, Zahlen, _ und - erlaubt'),
  email: z.string().email('Ungültige E-Mail-Adresse'),
  password: z
    .string()
    .min(8, 'Mindestens 8 Zeichen')
    .regex(/[A-Z]/, 'Mindestens ein Großbuchstabe')
    .regex(/[a-z]/, 'Mindestens ein Kleinbuchstabe')
    .regex(/[0-9]/, 'Mindestens eine Zahl'),
  first_name: z.string().min(1, 'Vorname ist erforderlich'),
  last_name: z.string().min(1, 'Nachname ist erforderlich'),
  phone_number: z.string().optional(),
  is_active: z.boolean().default(true),
  is_verified: z.boolean().default(true),
  role_ids: z.array(z.number()).default([]),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;

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

function VerifiedBadge({ isVerified }: { isVerified: boolean }) {
  return isVerified ? (
    <Badge variant="outline" className="gap-1 border-green-500 text-green-600">
      <CheckCircle className="h-3 w-3" />
      {t.admin.users.badges.verified}
    </Badge>
  ) : (
    <Badge variant="outline" className="gap-1 border-amber-500 text-amber-600">
      <XCircle className="h-3 w-3" />
      {t.admin.users.badges.unverified}
    </Badge>
  );
}

function TwoFactorBadge({ enabled }: { enabled: boolean }) {
  return enabled ? (
    <Badge variant="outline" className="gap-1 border-blue-500 text-blue-600">
      <Shield className="h-3 w-3" />
      {t.admin.users.badges.twoFactorOn}
    </Badge>
  ) : (
    <Badge variant="outline" className="gap-1">
      {t.admin.users.badges.twoFactorOff}
    </Badge>
  );
}

function LockedBadge({ lockedUntil }: { lockedUntil?: string }) {
  if (!lockedUntil) return null;

  const lockDate = new Date(lockedUntil);
  if (lockDate < new Date()) return null;

  return (
    <Badge variant="destructive" className="gap-1">
      <Lock className="h-3 w-3" />
      {t.admin.users.badges.locked}
    </Badge>
  );
}

function RoleBadges({ roles }: { roles: string[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {roles.map((role) => (
        <Badge key={role} variant="secondary" className="text-xs">
          {role}
        </Badge>
      ))}
    </div>
  );
}

function UserRow({ user, onView, onUnlock, onDeactivate, onActivate, onReset2FA, onResetPassword }: {
  user: AdminUser;
  onView: (userId: string) => void;
  onUnlock: (userId: string) => void;
  onDeactivate: (userId: string) => void;
  onActivate: (userId: string) => void;
  onReset2FA: (userId: string) => void;
  onResetPassword: (userId: string) => void;
}) {
  const isLocked = user.locked_until && new Date(user.locked_until) > new Date();

  return (
    <TableRow>
      <TableCell>
        <div>
          <p className="font-medium">{user.username}</p>
          <p className="text-sm text-muted-foreground">{user.email}</p>
        </div>
      </TableCell>
      <TableCell>
        {user.first_name} {user.last_name}
      </TableCell>
      <TableCell>
        <RoleBadges roles={user.roles} />
      </TableCell>
      <TableCell>
        <div className="flex flex-col gap-1">
          <StatusBadge isActive={user.is_active} />
          {isLocked && <LockedBadge lockedUntil={user.locked_until} />}
        </div>
      </TableCell>
      <TableCell>
        <TwoFactorBadge enabled={user.two_factor_enabled} />
      </TableCell>
      <TableCell>
        <VerifiedBadge isVerified={user.is_verified} />
      </TableCell>
      <TableCell>
        {user.last_login_at
          ? format(new Date(user.last_login_at), 'dd.MM.yyyy HH:mm', { locale: de })
          : '-'}
      </TableCell>
      <TableCell>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onView(user.user_id)}>
              <Eye className="mr-2 h-4 w-4" />
              {t.admin.users.actions.view}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onView(user.user_id)}>
              <Edit className="mr-2 h-4 w-4" />
              {t.admin.users.actions.edit}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onResetPassword(user.user_id)}>
              <Key className="mr-2 h-4 w-4" />
              {t.admin.users.actions.resetPassword || 'Passwort zurücksetzen'}
            </DropdownMenuItem>
            {user.two_factor_enabled && (
              <DropdownMenuItem onClick={() => onReset2FA(user.user_id)}>
                <ShieldOff className="mr-2 h-4 w-4" />
                {t.admin.users.actions.disable2FA || '2FA deaktivieren'}
              </DropdownMenuItem>
            )}
            {isLocked && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onUnlock(user.user_id)}>
                  <Unlock className="mr-2 h-4 w-4" />
                  {t.admin.users.actions.unlock}
                </DropdownMenuItem>
              </>
            )}
            <DropdownMenuSeparator />
            {user.is_active ? (
              <DropdownMenuItem
                onClick={() => onDeactivate(user.user_id)}
                className="text-destructive"
              >
                <UserX className="mr-2 h-4 w-4" />
                {t.admin.users.actions.deactivate}
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem onClick={() => onActivate(user.user_id)}>
                <UserCheck className="mr-2 h-4 w-4" />
                {t.admin.users.actions.activate}
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}

function CreateUserDialog({ roles, onClose }: { roles: Role[]; onClose: () => void }) {
  const createUser = useCreateUser();
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState<number[]>([]);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone_number: '',
      is_active: true,
      is_verified: true,
      role_ids: [],
    },
  });

  const password = watch('password', '');
  const isActive = watch('is_active', true);
  const isVerified = watch('is_verified', true);

  const passwordRequirements = [
    { label: 'Mindestens 8 Zeichen', met: password.length >= 8 },
    { label: 'Mindestens ein Großbuchstabe', met: /[A-Z]/.test(password) },
    { label: 'Mindestens ein Kleinbuchstabe', met: /[a-z]/.test(password) },
    { label: 'Mindestens eine Zahl', met: /[0-9]/.test(password) },
  ];

  const onSubmit = (data: CreateUserFormData) => {
    createUser.mutate(
      {
        ...data,
        role_ids: selectedRoles,
      },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  const toggleRole = (roleId: number) => {
    setSelectedRoles((prev) =>
      prev.includes(roleId)
        ? prev.filter((id) => id !== roleId)
        : [...prev, roleId]
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="first_name">{t.admin.users.createDialog.firstName}</Label>
          <Input
            id="first_name"
            placeholder={t.admin.users.createDialog.firstNamePlaceholder}
            {...register('first_name')}
          />
          {errors.first_name && (
            <p className="text-sm text-destructive">{errors.first_name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="last_name">{t.admin.users.createDialog.lastName}</Label>
          <Input
            id="last_name"
            placeholder={t.admin.users.createDialog.lastNamePlaceholder}
            {...register('last_name')}
          />
          {errors.last_name && (
            <p className="text-sm text-destructive">{errors.last_name.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="username">{t.admin.users.createDialog.username}</Label>
        <Input
          id="username"
          placeholder={t.admin.users.createDialog.usernamePlaceholder}
          {...register('username')}
        />
        {errors.username && (
          <p className="text-sm text-destructive">{errors.username.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">{t.admin.users.createDialog.email}</Label>
        <Input
          id="email"
          type="email"
          placeholder={t.admin.users.createDialog.emailPlaceholder}
          {...register('email')}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">{t.admin.users.createDialog.password}</Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder={t.admin.users.createDialog.passwordPlaceholder}
            {...register('password')}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-0 top-0 h-full px-3"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? 'Verbergen' : 'Anzeigen'}
          </Button>
        </div>
        {errors.password && (
          <p className="text-sm text-destructive">{errors.password.message}</p>
        )}
        {password && (
          <ul className="mt-2 space-y-1">
            {passwordRequirements.map((req, index) => (
              <li
                key={index}
                className={`flex items-center gap-2 text-xs ${
                  req.met ? 'text-green-600' : 'text-muted-foreground'
                }`}
              >
                {req.met ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                {req.label}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone_number">{t.admin.users.createDialog.phoneNumber}</Label>
        <Input
          id="phone_number"
          type="tel"
          placeholder={t.admin.users.createDialog.phoneNumberPlaceholder}
          {...register('phone_number')}
        />
      </div>

      {roles.length > 0 && (
        <div className="space-y-2">
          <Label>{t.admin.users.createDialog.roles}</Label>
          <div className="flex flex-wrap gap-2">
            {roles.map((role) => (
              <Badge
                key={role.role_id}
                variant={selectedRoles.includes(role.role_id) ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleRole(role.role_id)}
              >
                {selectedRoles.includes(role.role_id) && (
                  <Check className="mr-1 h-3 w-3" />
                )}
                {role.role_name}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-6">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_active"
            checked={isActive}
            onCheckedChange={(checked) => setValue('is_active', !!checked)}
          />
          <Label htmlFor="is_active" className="text-sm font-normal">
            {t.admin.users.createDialog.isActive}
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_verified"
            checked={isVerified}
            onCheckedChange={(checked) => setValue('is_verified', !!checked)}
          />
          <Label htmlFor="is_verified" className="text-sm font-normal">
            {t.admin.users.createDialog.isVerified}
          </Label>
        </div>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>
          {t.admin.users.createDialog.cancel}
        </Button>
        <Button type="submit" disabled={createUser.isPending}>
          {createUser.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {t.admin.users.createDialog.creating}
            </>
          ) : (
            t.admin.users.createDialog.create
          )}
        </Button>
      </DialogFooter>
    </form>
  );
}

export default function UsersPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isResetPasswordDialogOpen, setIsResetPasswordDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [filters, setFilters] = useState<{
    is_active?: boolean;
    is_verified?: boolean;
    two_factor_enabled?: boolean;
    is_locked?: boolean;
    role?: string;
  }>({});

  const { data: usersData, isLoading } = useUsers({
    page,
    page_size: 10,
    search: search || undefined,
    ...filters,
  });

  const { data: roles } = useRoles();
  const unlockUser = useUnlockUser();
  const deactivateUser = useDeactivateUser();
  const activateUser = useActivateUser();
  const reset2FA = useReset2FA();
  const resetPassword = useResetPassword();

  const users = usersData?.data || [];
  const pagination = usersData?.pagination;

  const handleView = (userId: string) => {
    router.push(`/admin/users/${userId}`);
  };

  const handleUnlock = (userId: string) => {
    unlockUser.mutate(userId);
  };

  const handleDeactivate = (userId: string) => {
    deactivateUser.mutate(userId);
  };

  const handleActivate = (userId: string) => {
    activateUser.mutate(userId);
  };

  const handleReset2FA = (userId: string) => {
    if (confirm('Sind Sie sicher, dass Sie die 2FA für diesen Benutzer deaktivieren möchten?')) {
      reset2FA.mutate(userId);
    }
  };

  const handleResetPassword = (userId: string) => {
    setSelectedUserId(userId);
    setNewPassword('');
    setIsResetPasswordDialogOpen(true);
  };

  const confirmResetPassword = () => {
    if (selectedUserId && newPassword.length >= 8) {
      resetPassword.mutate(
        { userId: selectedUserId, newPassword },
        {
          onSuccess: () => {
            setIsResetPasswordDialogOpen(false);
            setSelectedUserId(null);
            setNewPassword('');
          },
        }
      );
    }
  };

  const clearFilters = () => {
    setFilters({});
    setSearch('');
    setPage(1);
  };

  const hasActiveFilters = Object.keys(filters).length > 0 || search;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.admin.users.title} description={t.admin.users.subtitle} />
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.admin.users.title} description={t.admin.users.subtitle} />

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-lg">{t.admin.users.title}</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative flex-1 sm:w-64">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={t.admin.users.searchPlaceholder}
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="pl-9"
                />
              </div>
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <UserPlus className="mr-2 h-4 w-4" />
                    {t.admin.users.addUser}
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>{t.admin.users.createDialog.title}</DialogTitle>
                    <DialogDescription>
                      {t.admin.users.createDialog.subtitle}
                    </DialogDescription>
                  </DialogHeader>
                  <CreateUserDialog
                    roles={roles || []}
                    onClose={() => setIsCreateDialogOpen(false)}
                  />
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />

            <Select
              value={filters.is_active === undefined ? 'all' : filters.is_active ? 'active' : 'inactive'}
              onValueChange={(value) => {
                setFilters((prev) => ({
                  ...prev,
                  is_active: value === 'all' ? undefined : value === 'active',
                }));
                setPage(1);
              }}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder={t.admin.users.filters.status} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t.admin.users.filters.all}</SelectItem>
                <SelectItem value="active">{t.admin.users.filters.active}</SelectItem>
                <SelectItem value="inactive">{t.admin.users.filters.inactive}</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.two_factor_enabled === undefined ? 'all' : filters.two_factor_enabled ? 'enabled' : 'disabled'}
              onValueChange={(value) => {
                setFilters((prev) => ({
                  ...prev,
                  two_factor_enabled: value === 'all' ? undefined : value === 'enabled',
                }));
                setPage(1);
              }}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder={t.admin.users.filters.twoFactor} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t.admin.users.filters.all}</SelectItem>
                <SelectItem value="enabled">{t.admin.users.filters.enabled}</SelectItem>
                <SelectItem value="disabled">{t.admin.users.filters.disabled}</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.is_verified === undefined ? 'all' : filters.is_verified ? 'yes' : 'no'}
              onValueChange={(value) => {
                setFilters((prev) => ({
                  ...prev,
                  is_verified: value === 'all' ? undefined : value === 'yes',
                }));
                setPage(1);
              }}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder={t.admin.users.filters.verified} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t.admin.users.filters.all}</SelectItem>
                <SelectItem value="yes">{t.admin.users.filters.yes}</SelectItem>
                <SelectItem value="no">{t.admin.users.filters.no}</SelectItem>
              </SelectContent>
            </Select>

            {roles && roles.length > 0 && (
              <Select
                value={filters.role || 'all'}
                onValueChange={(value) => {
                  setFilters((prev) => ({
                    ...prev,
                    role: value === 'all' ? undefined : value,
                  }));
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder={t.admin.users.filters.role} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.admin.users.filters.all}</SelectItem>
                  {roles.map((role) => (
                    <SelectItem key={role.role_code} value={role.role_code}>
                      {role.role_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                {t.admin.users.filters.clearFilters}
              </Button>
            )}
          </div>

          {/* Table */}
          {users.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.admin.users.columns.username}</TableHead>
                      <TableHead>{t.admin.users.columns.fullName}</TableHead>
                      <TableHead>{t.admin.users.columns.roles}</TableHead>
                      <TableHead>{t.admin.users.columns.status}</TableHead>
                      <TableHead>{t.admin.users.columns.twoFactor}</TableHead>
                      <TableHead>{t.admin.users.columns.verified}</TableHead>
                      <TableHead>{t.admin.users.columns.lastLogin}</TableHead>
                      <TableHead className="w-12">{t.admin.users.columns.actions}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <UserRow
                        key={user.user_id}
                        user={user}
                        onView={handleView}
                        onUnlock={handleUnlock}
                        onDeactivate={handleDeactivate}
                        onActivate={handleActivate}
                        onReset2FA={handleReset2FA}
                        onResetPassword={handleResetPassword}
                      />
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {pagination && pagination.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Seite {pagination.page} von {pagination.total_pages} ({pagination.total_items} Benutzer)
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
              {t.admin.users.noUsers}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Password Reset Dialog */}
      <Dialog open={isResetPasswordDialogOpen} onOpenChange={setIsResetPasswordDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Passwort zurücksetzen</DialogTitle>
            <DialogDescription>
              Geben Sie ein neues Passwort für den Benutzer ein.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new_password">Neues Passwort</Label>
              <div className="relative">
                <Input
                  id="new_password"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Mindestens 8 Zeichen"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                >
                  {showNewPassword ? 'Verbergen' : 'Anzeigen'}
                </Button>
              </div>
              {newPassword && newPassword.length < 8 && (
                <p className="text-sm text-destructive">Passwort muss mindestens 8 Zeichen haben</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsResetPasswordDialogOpen(false)}>
              Abbrechen
            </Button>
            <Button
              onClick={confirmResetPassword}
              disabled={newPassword.length < 8 || resetPassword.isPending}
            >
              {resetPassword.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Wird zurückgesetzt...
                </>
              ) : (
                'Passwort zurücksetzen'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
