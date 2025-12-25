import Link from 'next/link';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { t } from '@/lib/translations';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="text-center space-y-6 max-w-md">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="rounded-full bg-muted p-6">
            <FileQuestion className="h-16 w-16 text-muted-foreground" />
          </div>
        </div>

        {/* Error Code */}
        <div className="space-y-2">
          <h1 className="text-7xl font-bold text-primary">{t.errors.notFound.code}</h1>
          <h2 className="text-2xl font-semibold">{t.errors.notFound.title}</h2>
          <p className="text-muted-foreground">
            {t.errors.notFound.description}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
          <Button asChild variant="default">
            <Link href="/dashboard">
              <ArrowLeft className="mr-2 h-4 w-4" />
              {t.errors.notFound.backToDashboard}
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              {t.errors.notFound.backHome}
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
