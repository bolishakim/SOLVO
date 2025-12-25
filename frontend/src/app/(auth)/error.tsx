'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { t } from '@/lib/translations';

export default function AuthError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Auth error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center space-y-6 py-12">
      {/* Icon */}
      <div className="rounded-full bg-destructive/10 p-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
      </div>

      {/* Error Message */}
      <div className="text-center space-y-2 max-w-sm">
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
      <div className="flex flex-col sm:flex-row gap-3">
        <Button onClick={reset} variant="default">
          <RefreshCw className="mr-2 h-4 w-4" />
          {t.errors.generic.tryAgain}
        </Button>
        <Button asChild variant="outline">
          <Link href="/login">
            <Home className="mr-2 h-4 w-4" />
            {t.auth.login.signIn}
          </Link>
        </Button>
      </div>
    </div>
  );
}
