'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw, Home, ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { t } from '@/lib/translations';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Dashboard error:', error);
  }, [error]);

  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="text-center space-y-6">
            {/* Icon */}
            <div className="flex justify-center">
              <div className="rounded-full bg-destructive/10 p-4">
                <AlertTriangle className="h-10 w-10 text-destructive" />
              </div>
            </div>

            {/* Error Message */}
            <div className="space-y-2">
              <h2 className="text-xl font-semibold">{t.errors.generic.title}</h2>
              <p className="text-sm text-muted-foreground">
                {t.errors.generic.description}
              </p>
              {error.digest && (
                <p className="text-xs text-muted-foreground font-mono">
                  Fehler-ID: {error.digest}
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-col gap-2 pt-2">
              <Button onClick={reset} variant="default" className="w-full">
                <RefreshCw className="mr-2 h-4 w-4" />
                {t.errors.generic.tryAgain}
              </Button>
              <Button asChild variant="outline" className="w-full">
                <Link href="/dashboard">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  {t.errors.notFound.backToDashboard}
                </Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
