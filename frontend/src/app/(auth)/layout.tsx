import { Recycle } from 'lucide-react';
import Link from 'next/link';
import { t } from '@/lib/translations';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex" suppressHydrationWarning>
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary text-primary-foreground flex-col justify-between p-12">
        <div className="flex items-center gap-2">
          <Recycle className="h-8 w-8" />
          <span className="text-xl font-bold">SOLVO GmbH</span>
        </div>

        <div className="space-y-6">
          <h1 className="text-4xl font-bold">
            Sicherheitstechnik und Personal für Schadstoffsanierung
          </h1>
          <p className="text-lg text-primary-foreground/80">
            SOLVO GmbH ist spezialisiert auf den Handel mit schadstoffspezifischen Produkten und Sicherheitstechnik für Asbest-, Mineralwolle- und andere Schadstoffsanierungen. Wir bieten persönliche Schutzausrüstung, Filtertechnik, Sanierungszubehör sowie geschultes Fachpersonal.
          </p>
          <ul className="space-y-3 text-primary-foreground/80">
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground/80" />
              Persönliche Schutzausrüstung (PSA)
            </li>
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground/80" />
              Unterdruckgeräte & Filtertechnik
            </li>
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground/80" />
              Schleusen- und Abschottungssysteme
            </li>
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground/80" />
              Qualifiziertes Fachpersonal
            </li>
          </ul>
        </div>

        <p className="text-sm text-primary-foreground/60">
          {t.app.copyright(new Date().getFullYear())}
        </p>
      </div>

      {/* Right side - Auth forms */}
      <div className="flex-1 flex flex-col">
        {/* Mobile header */}
        <div className="lg:hidden p-6 border-b">
          <Link href="/" className="flex items-center gap-2">
            <Recycle className="h-6 w-6 text-primary" />
            <span className="text-lg font-bold">SOLVO GmbH</span>
          </Link>
        </div>

        {/* Form container */}
        <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
          <div className="w-full max-w-md space-y-8">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
