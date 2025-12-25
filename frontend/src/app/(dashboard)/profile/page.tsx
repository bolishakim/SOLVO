'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import { useTheme } from 'next-themes';
import { User, Mail, Phone, Calendar, Clock, Shield, CheckCircle, XCircle, Sun, Moon, Monitor } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader } from '@/components/layout';
import { useProfile, useUpdateProfile } from '@/services/profile';
import { t } from '@/lib/translations';

const profileSchema = z.object({
  first_name: z.string().min(1, 'Vorname ist erforderlich'),
  last_name: z.string().min(1, 'Nachname ist erforderlich'),
  phone_number: z.string().optional().or(z.literal('')),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function ProfilePage() {
  const { data: user, isLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const [isEditing, setIsEditing] = useState(false);
  const { theme, setTheme } = useTheme();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone_number: user?.phone_number || '',
    },
  });

  // Update form when user data loads
  useEffect(() => {
    if (user && !isEditing) {
      reset({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone_number: user.phone_number || '',
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.user_id]);

  const onSubmit = async (data: ProfileFormData) => {
    await updateProfile.mutateAsync(data);
    setIsEditing(false);
  };

  const handleCancel = () => {
    if (user) {
      reset({
        first_name: user.first_name,
        last_name: user.last_name,
        phone_number: user.phone_number || '',
      });
    }
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.profile.title} description={t.profile.subtitle} />
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2">
            <CardHeader>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-64" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.profile.title} description={t.profile.subtitle} />

      <div className="grid gap-6 md:grid-cols-3">
        {/* Profile Form */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              {t.profile.personalInfo}
            </CardTitle>
            <CardDescription>{t.profile.personalInfoDescription}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="first_name">{t.profile.firstName}</Label>
                  <Input
                    id="first_name"
                    {...register('first_name')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                  {errors.first_name && (
                    <p className="text-sm text-destructive">{errors.first_name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">{t.profile.lastName}</Label>
                  <Input
                    id="last_name"
                    {...register('last_name')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                  {errors.last_name && (
                    <p className="text-sm text-destructive">{errors.last_name.message}</p>
                  )}
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="username">{t.profile.username}</Label>
                <Input
                  id="username"
                  value={user?.username || ''}
                  disabled
                  className="bg-muted"
                />
                <p className="text-xs text-muted-foreground">{t.profile.usernameHint}</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">{t.profile.email}</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="bg-muted pl-9"
                  />
                </div>
                <p className="text-xs text-muted-foreground">{t.profile.emailHint}</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone_number">{t.profile.phoneNumber}</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="phone_number"
                    {...register('phone_number')}
                    placeholder={t.profile.phoneNumberPlaceholder}
                    disabled={!isEditing}
                    className={`pl-9 ${!isEditing ? 'bg-muted' : ''}`}
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                {isEditing ? (
                  <>
                    <Button type="submit" disabled={updateProfile.isPending}>
                      {updateProfile.isPending ? t.profile.saving : t.profile.saveChanges}
                    </Button>
                    <Button type="button" variant="outline" onClick={handleCancel}>
                      {t.common.cancel}
                    </Button>
                  </>
                ) : (
                  <Button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setIsEditing(true);
                    }}
                  >
                    {t.common.edit}
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Account Info Sidebar */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              {t.profile.accountStatus}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Status</span>
              <Badge variant={user?.is_active ? 'default' : 'secondary'}>
                {user?.is_active ? t.profile.active : t.profile.inactive}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">E-Mail</span>
              {user?.is_verified ? (
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
              {user?.two_factor_enabled ? (
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

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">{t.profile.memberSince}:</span>
              </div>
              <p className="text-sm font-medium pl-6">
                {user?.created_at
                  ? format(new Date(user.created_at), 'dd. MMMM yyyy', { locale: de })
                  : '-'}
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">{t.profile.lastLogin}:</span>
              </div>
              <p className="text-sm font-medium pl-6">
                {user?.last_login_at
                  ? format(new Date(user.last_login_at), 'dd. MMMM yyyy, HH:mm', { locale: de })
                  : '-'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Theme Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sun className="h-5 w-5" />
            {t.settings.theme.title}
          </CardTitle>
          <CardDescription>{t.settings.theme.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button
              variant={theme === 'light' ? 'default' : 'outline'}
              className="flex items-center gap-2"
              onClick={() => setTheme('light')}
            >
              <Sun className="h-4 w-4" />
              {t.settings.theme.light}
            </Button>
            <Button
              variant={theme === 'dark' ? 'default' : 'outline'}
              className="flex items-center gap-2"
              onClick={() => setTheme('dark')}
            >
              <Moon className="h-4 w-4" />
              {t.settings.theme.dark}
            </Button>
            <Button
              variant={theme === 'system' ? 'default' : 'outline'}
              className="flex items-center gap-2"
              onClick={() => setTheme('system')}
            >
              <Monitor className="h-4 w-4" />
              {t.settings.theme.system}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
