'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Loader2, ArrowLeft, Shield, Key } from 'lucide-react';

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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useVerify2FA, useVerifyBackupCode } from '@/services/auth';
import { t } from '@/lib/translations';

export default function TwoFactorVerifyPage() {
  const router = useRouter();
  const [tempToken, setTempToken] = useState<string | null>(null);
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [backupCode, setBackupCode] = useState('');
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const verify2FA = useVerify2FA();
  const verifyBackupCode = useVerifyBackupCode();

  useEffect(() => {
    const token = sessionStorage.getItem('temp_token');
    if (!token) {
      router.replace('/login');
    } else {
      setTempToken(token);
    }
  }, [router]);

  const handleCodeChange = (index: number, value: string) => {
    if (value.length > 1) {
      // Handle paste
      const pastedCode = value.slice(0, 6).split('');
      const newCode = [...code];
      pastedCode.forEach((char, i) => {
        if (index + i < 6 && /^\d$/.test(char)) {
          newCode[index + i] = char;
        }
      });
      setCode(newCode);
      const nextIndex = Math.min(index + pastedCode.length, 5);
      inputRefs.current[nextIndex]?.focus();
    } else if (/^\d$/.test(value) || value === '') {
      const newCode = [...code];
      newCode[index] = value;
      setCode(newCode);

      if (value && index < 5) {
        inputRefs.current[index + 1]?.focus();
      }
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerifyCode = () => {
    if (tempToken && code.every((c) => c)) {
      verify2FA.mutate({
        temp_token: tempToken,
        code: code.join(''),
      });
    }
  };

  const handleVerifyBackupCode = () => {
    if (tempToken && backupCode) {
      verifyBackupCode.mutate({
        temp_token: tempToken,
        backup_code: backupCode.toUpperCase(),
      });
    }
  };

  const isCodeComplete = code.every((c) => c);

  if (!tempToken) {
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

  return (
    <Card className="border-0 shadow-lg">
      <CardHeader className="space-y-1 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Shield className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="text-2xl font-bold">{t.auth.twoFactor.title}</CardTitle>
        <CardDescription>
          {t.auth.twoFactor.subtitle}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="authenticator" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="authenticator">{t.auth.twoFactor.authenticator}</TabsTrigger>
            <TabsTrigger value="backup">{t.auth.twoFactor.backupCode}</TabsTrigger>
          </TabsList>

          <TabsContent value="authenticator" className="space-y-4 mt-4">
            <p className="text-sm text-muted-foreground text-center">
              {t.auth.twoFactor.enterCode}
            </p>

            <div className="flex justify-center gap-2">
              {code.map((digit, index) => (
                <Input
                  key={index}
                  ref={(el) => { inputRefs.current[index] = el; }}
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={digit}
                  onChange={(e) => handleCodeChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  className="w-12 h-12 text-center text-lg font-semibold"
                  disabled={verify2FA.isPending}
                  autoFocus={index === 0}
                />
              ))}
            </div>

            <Button
              className="w-full"
              onClick={handleVerifyCode}
              disabled={!isCodeComplete || verify2FA.isPending}
            >
              {verify2FA.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.auth.twoFactor.verifying}
                </>
              ) : (
                t.auth.twoFactor.verify
              )}
            </Button>
          </TabsContent>

          <TabsContent value="backup" className="space-y-4 mt-4">
            <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
              <Key className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              <p className="text-sm text-muted-foreground">
                {t.auth.twoFactor.useBackupCode}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="backup_code">{t.auth.twoFactor.backupCodeLabel}</Label>
              <Input
                id="backup_code"
                type="text"
                placeholder={t.auth.twoFactor.backupCodePlaceholder}
                value={backupCode}
                onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                className="font-mono text-center text-lg"
                disabled={verifyBackupCode.isPending}
              />
              <p className="text-xs text-muted-foreground text-center">
                {t.auth.twoFactor.backupCodeFormat}
              </p>
            </div>

            <Button
              className="w-full"
              onClick={handleVerifyBackupCode}
              disabled={!backupCode || verifyBackupCode.isPending}
            >
              {verifyBackupCode.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.auth.twoFactor.verifying}
                </>
              ) : (
                t.auth.twoFactor.useBackup
              )}
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
      <CardFooter className="flex justify-center">
        <Link
          href="/login"
          className="flex items-center gap-2 text-sm text-primary hover:underline"
          onClick={() => sessionStorage.removeItem('temp_token')}
        >
          <ArrowLeft className="h-4 w-4" />
          {t.auth.forgotPassword.backToLogin}
        </Link>
      </CardFooter>
    </Card>
  );
}
