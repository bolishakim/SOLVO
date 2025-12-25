'use client';

import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader } from '@/components/layout';
import { useCurrentUser } from '@/services/auth';
import { useWorkflows, getWorkflowWithMeta, type Workflow } from '@/services/workflows';
import { t } from '@/lib/translations';
import {
  Truck,
  Box,
  ArrowRight,
  Clock,
  Receipt,
} from 'lucide-react';

// Icon mapping for workflows
const WORKFLOW_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Truck: Truck,
  Box: Box,
  Clock: Clock,
  Receipt: Receipt,
};

export default function DashboardPage() {
  const { data: user } = useCurrentUser();
  const { data: workflows, isLoading: workflowsLoading } = useWorkflows();

  return (
    <div className="space-y-8">
      <PageHeader
        title={t.dashboard.welcome(user?.first_name || 'Benutzer')}
        description={t.workflows.subtitle}
      />

      {/* Workflows Grid */}
      <section>
        {workflowsLoading ? (
          <div className="flex flex-wrap gap-6">
            {[1, 2, 3].map((i) => (
              <WorkflowCardSkeleton key={i} />
            ))}
          </div>
        ) : workflows && workflows.length > 0 ? (
          <div className="flex flex-wrap gap-6">
            {workflows.map((workflow) => (
              <WorkflowCard key={workflow.workflow_id} workflow={workflow} />
            ))}
          </div>
        ) : (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Box className="h-16 w-16 text-muted-foreground/50 mb-4" />
              <p className="text-muted-foreground text-center text-lg">
                {t.workflows.noWorkflows}
              </p>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  );
}

function WorkflowCard({ workflow }: { workflow: Workflow }) {
  const workflowWithMeta = getWorkflowWithMeta(workflow);
  const IconComponent = WORKFLOW_ICONS[workflowWithMeta.meta.icon] || Box;

  return (
    <Link href={workflowWithMeta.meta.href}>
      <Card className="group relative overflow-hidden cursor-pointer transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 hover:border-primary/50 w-56 h-56">
        {/* Background gradient */}
        <div className={`absolute inset-0 ${workflowWithMeta.meta.color} opacity-5 group-hover:opacity-10 transition-opacity`} />

        <CardContent className="flex flex-col items-center justify-center h-full p-4 relative">
          {/* Icon */}
          <div className={`p-4 rounded-2xl ${workflowWithMeta.meta.color} mb-4 group-hover:scale-110 transition-transform duration-300`}>
            <IconComponent className="h-10 w-10 text-white" />
          </div>

          {/* Workflow Name */}
          <h3 className="text-base font-medium text-center text-foreground/80 group-hover:text-primary transition-colors leading-snug tracking-tight">
            {workflow.workflow_name}
          </h3>

          {/* Arrow indicator on hover */}
          <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <ArrowRight className="h-4 w-4 text-primary" />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function WorkflowCardSkeleton() {
  return (
    <Card className="w-56 h-56">
      <CardContent className="flex flex-col items-center justify-center h-full p-4">
        <Skeleton className="h-16 w-16 rounded-2xl mb-4" />
        <Skeleton className="h-4 w-28" />
      </CardContent>
    </Card>
  );
}
