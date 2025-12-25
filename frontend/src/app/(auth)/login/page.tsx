'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { loginSchema, type LoginFormData } from '@/lib/validations';
import { useLogin } from '@/services/auth';
import { t } from '@/lib/translations';

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const login = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username_or_email: '',
      password: '',
    },
  });

  const onSubmit = (data: LoginFormData) => {
    login.mutate(data);
  };

  return (
    <Card className="border-0 shadow-none bg-transparent">
      <CardHeader className="space-y-1 text-center">
        <CardTitle className="text-2xl font-bold">{t.auth.login.title}</CardTitle>
        <CardDescription>
          {t.auth.login.subtitle}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username_or_email">{t.auth.login.usernameOrEmail}</Label>
            <Input
              id="username_or_email"
              type="text"
              placeholder={t.auth.login.usernameOrEmailPlaceholder}
              autoComplete="username"
              disabled={login.isPending}
              {...register('username_or_email')}
            />
            {errors.username_or_email && (
              <p className="text-sm text-destructive">
                {errors.username_or_email.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">{t.auth.login.password}</Label>
              <Link
                href="/forgot-password"
                className="text-sm text-primary hover:underline"
              >
                {t.auth.login.forgotPassword}
              </Link>
            </div>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder={t.auth.login.passwordPlaceholder}
                autoComplete="current-password"
                disabled={login.isPending}
                {...register('password')}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
                disabled={login.isPending}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
                <span className="sr-only">
                  {showPassword ? 'Passwort verbergen' : 'Passwort anzeigen'}
                </span>
              </Button>
            </div>
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={login.isPending}>
            {login.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.auth.login.signingIn}
              </>
            ) : (
              t.auth.login.signIn
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
