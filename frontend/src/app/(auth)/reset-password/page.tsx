'use client';

import { Suspense, useState, useEffect } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Loader2, ArrowLeft, Check, X, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { resetPasswordSchema, type ResetPasswordFormData } from '@/lib/validations';
import { useResetPassword } from '@/services/auth';
import { t } from '@/lib/translations';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const resetPassword = useResetPassword();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      token: '',
      new_password: '',
      confirm_password: '',
    },
  });

  useEffect(() => {
    if (token) {
      setValue('token', token);
    }
  }, [token, setValue]);

  const password = watch('new_password', '');

  const passwordRequirements = [
    { label: t.auth.register.passwordRequirements.minLength, met: password.length >= 8 },
    { label: t.auth.register.passwordRequirements.uppercase, met: /[A-Z]/.test(password) },
    { label: t.auth.register.passwordRequirements.lowercase, met: /[a-z]/.test(password) },
    { label: t.auth.register.passwordRequirements.number, met: /[0-9]/.test(password) },
  ];

  const onSubmit = (data: ResetPasswordFormData) => {
    resetPassword.mutate({
      token: data.token,
      new_password: data.new_password,
    });
  };

  if (!token) {
    return (
      <Card className="border-0 shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle className="text-2xl font-bold">{t.auth.resetPassword.invalidLink}</CardTitle>
          <CardDescription>
            {t.auth.resetPassword.linkExpired}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button asChild className="w-full">
            <Link href="/forgot-password">{t.auth.resetPassword.requestNewLink}</Link>
          </Button>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Link
            href="/login"
            className="flex items-center gap-2 text-sm text-primary hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            {t.auth.forgotPassword.backToLogin}
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-lg">
      <CardHeader className="space-y-1 text-center">
        <CardTitle className="text-2xl font-bold">{t.auth.resetPassword.title}</CardTitle>
        <CardDescription>
          {t.auth.resetPassword.subtitle}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <input type="hidden" {...register('token')} />

          <div className="space-y-2">
            <Label htmlFor="new_password">{t.auth.resetPassword.newPassword}</Label>
            <div className="relative">
              <Input
                id="new_password"
                type={showPassword ? 'text' : 'password'}
                placeholder={t.auth.resetPassword.newPasswordPlaceholder}
                autoComplete="new-password"
                disabled={resetPassword.isPending}
                {...register('new_password')}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
                disabled={resetPassword.isPending}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
            {errors.new_password && (
              <p className="text-sm text-destructive">
                {errors.new_password.message}
              </p>
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
                    {req.met ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      <X className="h-3 w-3" />
                    )}
                    {req.label}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">{t.auth.resetPassword.confirmPassword}</Label>
            <div className="relative">
              <Input
                id="confirm_password"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder={t.auth.resetPassword.confirmPasswordPlaceholder}
                autoComplete="new-password"
                disabled={resetPassword.isPending}
                {...register('confirm_password')}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                disabled={resetPassword.isPending}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
            {errors.confirm_password && (
              <p className="text-sm text-destructive">
                {errors.confirm_password.message}
              </p>
            )}
          </div>

          {errors.token && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{errors.token.message}</AlertDescription>
            </Alert>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={resetPassword.isPending}
          >
            {resetPassword.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.auth.resetPassword.resettingPassword}
              </>
            ) : (
              t.auth.resetPassword.resetPassword
            )}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="flex justify-center">
        <Link
          href="/login"
          className="flex items-center gap-2 text-sm text-primary hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          {t.auth.forgotPassword.backToLogin}
        </Link>
      </CardFooter>
    </Card>
  );
}

function LoadingCard() {
  return (
    <Card className="border-0 shadow-lg">
      <CardHeader className="space-y-1 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
        <CardTitle className="text-2xl font-bold">{t.auth.loading}</CardTitle>
      </CardHeader>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<LoadingCard />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
