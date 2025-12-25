'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  Clock,
  MapPin,
  Trash2,
  Loader2,
  CheckCircle,
} from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { PageHeader } from '@/components/layout';
import { useSessions, useRevokeSession, useRevokeAllSessions } from '@/services/profile';
import { t } from '@/lib/translations';
import type { Session } from '@/types';

function parseUserAgent(userAgent: string): { device: string; browser: string; icon: React.ComponentType<{ className?: string }> } {
  const ua = userAgent.toLowerCase();

  // Determine device type
  let device = 'Desktop';
  let icon: React.ComponentType<{ className?: string }> = Monitor;

  if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
    device = 'Smartphone';
    icon = Smartphone;
  } else if (ua.includes('tablet') || ua.includes('ipad')) {
    device = 'Tablet';
    icon = Tablet;
  }

  // Determine browser
  let browser = 'Unbekannt';
  if (ua.includes('firefox')) {
    browser = 'Firefox';
  } else if (ua.includes('edg')) {
    browser = 'Edge';
  } else if (ua.includes('chrome')) {
    browser = 'Chrome';
  } else if (ua.includes('safari')) {
    browser = 'Safari';
  } else if (ua.includes('opera') || ua.includes('opr')) {
    browser = 'Opera';
  }

  return { device, browser, icon };
}

function SessionCard({
  session,
  isCurrentSession,
  onRevoke,
  isRevoking,
}: {
  session: Session;
  isCurrentSession: boolean;
  onRevoke: () => void;
  isRevoking: boolean;
}) {
  const { device, browser, icon: DeviceIcon } = parseUserAgent(session.user_agent);

  return (
    <Card className={isCurrentSession ? 'border-primary' : ''}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="rounded-full bg-muted p-3">
              <DeviceIcon className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">{device}</span>
                {isCurrentSession && (
                  <Badge variant="default" className="gap-1">
                    <CheckCircle className="h-3 w-3" />
                    {t.sessions.thisDevice}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground">{browser}</p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Globe className="h-3 w-3" />
                  {session.ip_address}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {t.sessions.createdAt}: {format(new Date(session.created_at), 'dd.MM.yyyy HH:mm', { locale: de })}
                </span>
              </div>
              {session.last_activity_at && (
                <p className="text-xs text-muted-foreground">
                  {t.sessions.lastActive}: {format(new Date(session.last_activity_at), 'dd.MM.yyyy HH:mm', { locale: de })}
                </p>
              )}
            </div>
          </div>
          {!isCurrentSession && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRevoke}
              disabled={isRevoking}
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
            >
              {isRevoking ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Trash2 className="mr-1 h-4 w-4" />
                  {t.sessions.revoke}
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function SessionsPage() {
  const { data: sessionsData, isLoading } = useSessions();
  const revokeSession = useRevokeSession();
  const revokeAllSessions = useRevokeAllSessions();

  const [sessionToRevoke, setSessionToRevoke] = useState<number | null>(null);
  const [showRevokeAllDialog, setShowRevokeAllDialog] = useState(false);

  const sessions = sessionsData?.sessions || [];
  const currentSessionId = sessionsData?.current_session_id;

  const currentSession = sessions.find(s => s.session_id === currentSessionId);
  const otherSessions = sessions.filter(s => s.session_id !== currentSessionId);

  const handleRevokeSession = async (sessionId: number) => {
    await revokeSession.mutateAsync(sessionId);
    setSessionToRevoke(null);
  };

  const handleRevokeAllSessions = async () => {
    await revokeAllSessions.mutateAsync();
    setShowRevokeAllDialog(false);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.sessions.title} description={t.sessions.subtitle} />
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.sessions.title} description={t.sessions.subtitle} />

      {/* Current Session */}
      {currentSession && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">{t.sessions.currentSession}</h3>
          <SessionCard
            session={currentSession}
            isCurrentSession={true}
            onRevoke={() => {}}
            isRevoking={false}
          />
        </div>
      )}

      {/* Other Sessions */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-muted-foreground">{t.sessions.otherSessions}</h3>
          {otherSessions.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowRevokeAllDialog(true)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="mr-1 h-4 w-4" />
              {t.sessions.revokeAll}
            </Button>
          )}
        </div>
        {otherSessions.length > 0 ? (
          <div className="space-y-3">
            {otherSessions.map((session) => (
              <SessionCard
                key={session.session_id}
                session={session}
                isCurrentSession={false}
                onRevoke={() => setSessionToRevoke(session.session_id)}
                isRevoking={revokeSession.isPending && sessionToRevoke === session.session_id}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              {t.sessions.noOtherSessions}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Revoke Single Session Dialog */}
      <AlertDialog open={sessionToRevoke !== null} onOpenChange={() => setSessionToRevoke(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.sessions.revokeConfirm}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.sessions.revokeConfirmDescription}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => sessionToRevoke && handleRevokeSession(sessionToRevoke)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {revokeSession.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              {t.sessions.revoke}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Revoke All Sessions Dialog */}
      <AlertDialog open={showRevokeAllDialog} onOpenChange={setShowRevokeAllDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.sessions.revokeAllConfirm}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.sessions.revokeAllConfirmDescription}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRevokeAllSessions}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {revokeAllSessions.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              {t.sessions.revokeAll}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
