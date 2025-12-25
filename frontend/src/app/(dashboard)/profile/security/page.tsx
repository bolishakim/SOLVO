'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Lock,
  Shield,
  ShieldCheck,
  ShieldOff,
  Eye,
  EyeOff,
  Copy,
  Check,
  Download,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Alert,
  AlertDescription,
} from '@/components/ui/alert';
import { PageHeader } from '@/components/layout';
import { useChangePassword } from '@/services/auth';
import {
  useProfile,
  use2FAStatus,
  useSetup2FA,
  useEnable2FA,
  useDisable2FA,
  useRegenerateBackupCodes,
} from '@/services/profile';
import { t } from '@/lib/translations';

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Aktuelles Passwort ist erforderlich'),
  new_password: z
    .string()
    .min(8, 'Passwort muss mindestens 8 Zeichen haben')
    .regex(/[A-Z]/, 'Passwort muss mindestens einen Großbuchstaben enthalten')
    .regex(/[a-z]/, 'Passwort muss mindestens einen Kleinbuchstaben enthalten')
    .regex(/[0-9]/, 'Passwort muss mindestens eine Zahl enthalten'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Passwörter stimmen nicht überein',
  path: ['confirm_password'],
});

type PasswordFormData = z.infer<typeof passwordSchema>;

export default function SecurityPage() {
  const { data: user, isLoading: userLoading } = useProfile();
  const { data: twoFactorStatus, isLoading: twoFactorLoading } = use2FAStatus();
  const changePassword = useChangePassword();
  const setup2FA = useSetup2FA();
  const enable2FA = useEnable2FA();
  const disable2FA = useDisable2FA();
  const regenerateBackupCodes = useRegenerateBackupCodes();

  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [show2FASetupDialog, setShow2FASetupDialog] = useState(false);
  const [show2FADisableDialog, setShow2FADisableDialog] = useState(false);
  const [showBackupCodesDialog, setShowBackupCodesDialog] = useState(false);

  const [verificationCode, setVerificationCode] = useState('');
  const [disablePassword, setDisablePassword] = useState('');
  const [showDisablePassword, setShowDisablePassword] = useState(false);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  const onPasswordSubmit = async (data: PasswordFormData) => {
    await changePassword.mutateAsync({
      current_password: data.current_password,
      new_password: data.new_password,
    });
    reset();
  };

  const handleSetup2FA = async () => {
    await setup2FA.mutateAsync();
    setShow2FASetupDialog(true);
  };

  const handleEnable2FA = async () => {
    const result = await enable2FA.mutateAsync(verificationCode);
    setShow2FASetupDialog(false);
    setVerificationCode('');
    if (result.data.backup_codes) {
      setBackupCodes(result.data.backup_codes);
      setShowBackupCodesDialog(true);
    }
  };

  const handleDisable2FA = async () => {
    await disable2FA.mutateAsync({ code: verificationCode, password: disablePassword });
    setShow2FADisableDialog(false);
    setVerificationCode('');
    setDisablePassword('');
  };

  const handleRegenerateBackupCodes = async () => {
    const result = await regenerateBackupCodes.mutateAsync();
    if (result.data.backup_codes) {
      setBackupCodes(result.data.backup_codes);
      setShowBackupCodesDialog(true);
    }
  };

  const copyToClipboard = async (code: string) => {
    await navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const downloadBackupCodes = () => {
    const content = backupCodes.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const isLoading = userLoading || twoFactorLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.security.title} description={t.security.subtitle} />
        <div className="grid gap-6">
          <Card>
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
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-64" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.security.title} description={t.security.subtitle} />

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            {t.security.changePassword}
          </CardTitle>
          <CardDescription>{t.security.changePasswordDescription}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onPasswordSubmit)} className="space-y-4 max-w-md">
            <div className="space-y-2">
              <Label htmlFor="current_password">{t.security.currentPassword}</Label>
              <div className="relative">
                <Input
                  id="current_password"
                  type={showCurrentPassword ? 'text' : 'password'}
                  placeholder={t.security.currentPasswordPlaceholder}
                  {...register('current_password')}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                >
                  {showCurrentPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {errors.current_password && (
                <p className="text-sm text-destructive">{errors.current_password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="new_password">{t.security.newPassword}</Label>
              <div className="relative">
                <Input
                  id="new_password"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder={t.security.newPasswordPlaceholder}
                  {...register('new_password')}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                >
                  {showNewPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {errors.new_password && (
                <p className="text-sm text-destructive">{errors.new_password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm_password">{t.security.confirmNewPassword}</Label>
              <div className="relative">
                <Input
                  id="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder={t.security.confirmNewPasswordPlaceholder}
                  {...register('confirm_password')}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {errors.confirm_password && (
                <p className="text-sm text-destructive">{errors.confirm_password.message}</p>
              )}
            </div>

            <Button type="submit" disabled={changePassword.isPending}>
              {changePassword.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.security.updatingPassword}
                </>
              ) : (
                t.security.updatePassword
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Two-Factor Authentication */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                {t.security.twoFactor}
              </CardTitle>
              <CardDescription>{t.security.twoFactorDescription}</CardDescription>
            </div>
            {user?.two_factor_enabled ? (
              <Badge variant="default" className="gap-1">
                <ShieldCheck className="h-3 w-3" />
                {t.security.twoFactorEnabled}
              </Badge>
            ) : (
              <Badge variant="secondary" className="gap-1">
                <ShieldOff className="h-3 w-3" />
                {t.security.twoFactorDisabled}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {user?.two_factor_enabled ? (
            <div className="space-y-4">
              <Alert>
                <ShieldCheck className="h-4 w-4" />
                <AlertDescription>
                  {t.security.backupCodesRemaining(twoFactorStatus?.backup_codes_remaining || 0)}
                </AlertDescription>
              </Alert>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleRegenerateBackupCodes}
                  disabled={regenerateBackupCodes.isPending}
                >
                  {regenerateBackupCodes.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  {t.security.regenerateCodes}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => setShow2FADisableDialog(true)}
                >
                  {t.security.disable2FA}
                </Button>
              </div>
            </div>
          ) : (
            <Button onClick={handleSetup2FA} disabled={setup2FA.isPending}>
              {setup2FA.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Shield className="mr-2 h-4 w-4" />
              )}
              {t.security.enable2FA}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* 2FA Setup Dialog */}
      <Dialog open={show2FASetupDialog} onOpenChange={setShow2FASetupDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t.security.setup2FA}</DialogTitle>
            <DialogDescription>{t.security.setup2FADescription}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {setup2FA.data?.data && (
              <>
                <div className="flex justify-center">
                  <div className="rounded-lg bg-white p-4">
                    {setup2FA.data.data.qr_code_uri ? (
                      <QRCodeSVG
                        value={setup2FA.data.data.qr_code_uri}
                        size={192}
                        level="M"
                        includeMargin={false}
                      />
                    ) : (
                      <div className="h-48 w-48 bg-muted flex items-center justify-center text-xs text-muted-foreground">
                        QR Code nicht verfügbar
                      </div>
                    )}
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">{t.security.manualEntry}</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 rounded bg-muted px-3 py-2 text-sm font-mono">
                      {setup2FA.data.data.manual_entry_key}
                    </code>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => copyToClipboard(setup2FA.data.data.manual_entry_key)}
                    >
                      {copiedCode === setup2FA.data.data.manual_entry_key ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </>
            )}
            <Separator />
            <div className="space-y-2">
              <Label>{t.security.enterCodeToEnable}</Label>
              <Input
                placeholder={t.security.verificationCodePlaceholder}
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShow2FASetupDialog(false)}>
              {t.common.cancel}
            </Button>
            <Button
              onClick={handleEnable2FA}
              disabled={verificationCode.length !== 6 || enable2FA.isPending}
            >
              {enable2FA.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              {t.security.enable2FA}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 2FA Disable Dialog */}
      <Dialog open={show2FADisableDialog} onOpenChange={(open) => {
        setShow2FADisableDialog(open);
        if (!open) {
          setVerificationCode('');
          setDisablePassword('');
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t.security.disable2FA}</DialogTitle>
            <DialogDescription>{t.security.enterCodeToDisable}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>{t.security.verificationCode}</Label>
              <Input
                placeholder={t.security.verificationCodePlaceholder}
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
              />
            </div>
            <div className="space-y-2">
              <Label>{t.security.currentPassword}</Label>
              <div className="relative">
                <Input
                  type={showDisablePassword ? 'text' : 'password'}
                  placeholder={t.security.currentPasswordPlaceholder}
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowDisablePassword(!showDisablePassword)}
                >
                  {showDisablePassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShow2FADisableDialog(false)}>
              {t.common.cancel}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDisable2FA}
              disabled={verificationCode.length !== 6 || !disablePassword || disable2FA.isPending}
            >
              {disable2FA.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              {t.security.disable2FA}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backup Codes Dialog */}
      <Dialog open={showBackupCodesDialog} onOpenChange={setShowBackupCodesDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t.security.backupCodes}</DialogTitle>
            <DialogDescription>{t.security.backupCodesDescription}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              {backupCodes.map((code, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded bg-muted px-3 py-2"
                >
                  <code className="text-sm font-mono">{code}</code>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => copyToClipboard(code)}
                  >
                    {copiedCode === code ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={downloadBackupCodes}>
              <Download className="mr-2 h-4 w-4" />
              {t.security.downloadCodes}
            </Button>
            <Button onClick={() => setShowBackupCodesDialog(false)}>
              {t.common.close}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
