'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Loader2, ArrowLeft, CheckCircle, XCircle, Mail } from 'lucide-react';

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
import { useVerifyEmail, useResendVerification } from '@/services/auth';
import { t } from '@/lib/translations';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [email, setEmail] = useState('');
  const [verificationStatus, setVerificationStatus] = useState<
    'pending' | 'verifying' | 'success' | 'error' | 'no-token'
  >(token ? 'pending' : 'no-token');

  const verifyEmail = useVerifyEmail();
  const resendVerification = useResendVerification();

  useEffect(() => {
    if (token && verificationStatus === 'pending') {
      setVerificationStatus('verifying');
      verifyEmail.mutate(token, {
        onSuccess: () => {
          setVerificationStatus('success');
        },
        onError: () => {
          setVerificationStatus('error');
        },
      });
    }
  }, [token]);

  const handleResend = () => {
    if (email) {
      resendVerification.mutate(email);
    }
  };

  // Verifying state
  if (verificationStatus === 'verifying') {
    return (
      <Card className="border-0 shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">{t.auth.verifyEmail.verifying}</CardTitle>
          <CardDescription>
            {t.auth.verifyEmail.verifyingSubtitle}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Success state
  if (verificationStatus === 'success') {
    return (
      <Card className="border-0 shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <CardTitle className="text-2xl font-bold">{t.auth.verifyEmail.verified}</CardTitle>
          <CardDescription>
            {t.auth.verifyEmail.verifiedSubtitle}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full">
            <Link href="/login">{t.auth.verifyEmail.continueToLogin}</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (verificationStatus === 'error') {
    return (
      <Card className="border-0 shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <XCircle className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle className="text-2xl font-bold">{t.auth.verifyEmail.verificationFailed}</CardTitle>
          <CardDescription>
            {t.auth.verifyEmail.verificationFailedSubtitle}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground text-center">
            {t.auth.verifyEmail.enterEmailForNew}
          </p>
          <div className="space-y-2">
            <Label htmlFor="email">{t.auth.forgotPassword.email}</Label>
            <Input
              id="email"
              type="email"
              placeholder={t.auth.forgotPassword.emailPlaceholder}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={resendVerification.isPending}
            />
          </div>
          <Button
            className="w-full"
            onClick={handleResend}
            disabled={!email || resendVerification.isPending}
          >
            {resendVerification.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.auth.verifyEmail.sending}
              </>
            ) : (
              t.auth.verifyEmail.resendVerification
            )}
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

  // No token - show resend form
  return (
    <Card className="border-0 shadow-lg">
      <CardHeader className="space-y-1 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Mail className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="text-2xl font-bold">{t.auth.verifyEmail.title}</CardTitle>
        <CardDescription>
          {t.auth.verifyEmail.subtitle}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">{t.auth.forgotPassword.email}</Label>
          <Input
            id="email"
            type="email"
            placeholder={t.auth.forgotPassword.emailPlaceholder}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={resendVerification.isPending}
          />
        </div>
        <Button
          className="w-full"
          onClick={handleResend}
          disabled={!email || resendVerification.isPending}
        >
          {resendVerification.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {t.auth.verifyEmail.sending}
            </>
          ) : (
            t.auth.verifyEmail.sendVerification
          )}
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

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<LoadingCard />}>
      <VerifyEmailContent />
    </Suspense>
  );
}
