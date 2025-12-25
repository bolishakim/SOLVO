'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/layout';
import { t } from '@/lib/translations';
import {
  FileText,
  Scale,
  AlertTriangle,
  Building2,
  Briefcase,
  MapPin,
  Boxes,
  Download,
  TrendingUp,
  TrendingDown,
  ArrowRight,
} from 'lucide-react';

// Stat cards data for the workflow dashboard
const statCards = [
  {
    title: t.workflows.stats.documents,
    value: '1,284',
    change: '+12%',
    trend: 'up' as const,
    href: '/landfill/documents',
    icon: FileText,
    color: 'bg-blue-500',
  },
  {
    title: t.workflows.stats.weighSlips,
    value: '3,456',
    change: '+8%',
    trend: 'up' as const,
    href: '/landfill/weigh-slips',
    icon: Scale,
    color: 'bg-emerald-500',
  },
  {
    title: t.nav.hazardousSlips,
    value: '89',
    change: '-3%',
    trend: 'down' as const,
    href: '/landfill/hazardous-slips',
    icon: AlertTriangle,
    color: 'bg-amber-500',
  },
  {
    title: t.workflows.stats.sites,
    value: '24',
    change: '+2',
    trend: 'up' as const,
    href: '/landfill/sites',
    icon: Building2,
    color: 'bg-violet-500',
  },
];

// Quick access cards
const quickAccessCards = [
  {
    title: t.nav.companies,
    description: t.pages.companies.description,
    href: '/landfill/companies',
    icon: Briefcase,
    color: 'bg-pink-500',
  },
  {
    title: t.nav.locations,
    description: t.pages.locations.description,
    href: '/landfill/locations',
    icon: MapPin,
    color: 'bg-cyan-500',
  },
  {
    title: t.nav.materials,
    description: t.pages.materials.description,
    href: '/landfill/materials',
    icon: Boxes,
    color: 'bg-orange-500',
  },
  {
    title: t.nav.export,
    description: t.pages.export.description,
    href: '/landfill/export',
    icon: Download,
    color: 'bg-slate-500',
  },
];

export default function LandfillDashboardPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Deponie"
        description="Übersicht und Verwaltung der Deponie-Daten"
      />

      {/* Stats Grid */}
      <section>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => (
            <StatCard key={stat.href} {...stat} />
          ))}
        </div>
      </section>

      {/* Quick Access Section */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Schnellzugriff</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickAccessCards.map((card) => (
            <QuickAccessCard key={card.href} {...card} />
          ))}
        </div>
      </section>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

function StatCard({ title, value, change, trend, href, icon: Icon, color }: StatCardProps) {
  return (
    <Link href={href}>
      <Card className="group cursor-pointer transition-all hover:shadow-md hover:border-primary/50">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <div className={`p-2 rounded-lg ${color}`}>
            <Icon className="h-4 w-4 text-white" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-end justify-between">
            <div>
              <div className="text-2xl font-bold">{value}</div>
              <div className={`flex items-center text-xs ${
                trend === 'up' ? 'text-emerald-600' : 'text-red-600'
              }`}>
                {trend === 'up' ? (
                  <TrendingUp className="h-3 w-3 mr-1" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1" />
                )}
                {change}
              </div>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

interface QuickAccessCardProps {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

function QuickAccessCard({ title, description, href, icon: Icon, color }: QuickAccessCardProps) {
  return (
    <Link href={href}>
      <Card className="group cursor-pointer transition-all hover:shadow-md hover:border-primary/50 h-full">
        <CardContent className="flex items-start gap-4 p-4">
          <div className={`p-3 rounded-lg ${color} shrink-0`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-sm group-hover:text-primary transition-colors">
              {title}
            </h3>
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {description}
            </p>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 transition-opacity mt-1" />
        </CardContent>
      </Card>
    </Link>
  );
}
