'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowLeft, Mail } from 'lucide-react';

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
import { forgotPasswordSchema, type ForgotPasswordFormData } from '@/lib/validations';
import { useForgotPassword } from '@/services/auth';
import { t } from '@/lib/translations';

export default function ForgotPasswordPage() {
  const [emailSent, setEmailSent] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');
  const forgotPassword = useForgotPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = (data: ForgotPasswordFormData) => {
    setSubmittedEmail(data.email);
    forgotPassword.mutate(data.email, {
      onSuccess: () => {
        setEmailSent(true);
      },
    });
  };

  if (emailSent) {
    return (
      <Card className="border-0 shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <Mail className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">{t.auth.forgotPassword.checkEmail}</CardTitle>
          <CardDescription>
            {t.auth.forgotPassword.emailSentTo}{' '}
            <span className="font-medium text-foreground">{submittedEmail}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground text-center">
            {t.auth.forgotPassword.didntReceive}
          </p>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => {
              setEmailSent(false);
              setSubmittedEmail('');
            }}
          >
            {t.auth.forgotPassword.tryDifferentEmail}
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
        <CardTitle className="text-2xl font-bold">{t.auth.forgotPassword.title}</CardTitle>
        <CardDescription>
          {t.auth.forgotPassword.subtitle}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">{t.auth.forgotPassword.email}</Label>
            <Input
              id="email"
              type="email"
              placeholder={t.auth.forgotPassword.emailPlaceholder}
              autoComplete="email"
              disabled={forgotPassword.isPending}
              {...register('email')}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={forgotPassword.isPending}
          >
            {forgotPassword.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.auth.forgotPassword.sendingResetLink}
              </>
            ) : (
              t.auth.forgotPassword.sendResetLink
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
