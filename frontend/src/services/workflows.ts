import api from '@/lib/api';
import { useQuery } from '@tanstack/react-query';
import type { ApiResponse } from '@/types/api';

// Types
export interface Workflow {
  workflow_id: number;
  workflow_name: string;
  workflow_code: string;
  description: string | null;
  is_active: boolean;
  created_at: string | null;
}

// Quick link for workflow navigation
export interface WorkflowLink {
  labelKey: string; // Key in translations
  href: string;
  icon: string; // Lucide icon name
}

// Workflow metadata for frontend display
export interface WorkflowMeta {
  code: string;
  icon: string; // Lucide icon name
  color: string; // Tailwind color class
  href: string; // Navigation path
  links: WorkflowLink[]; // Quick navigation links
}

// Map workflow codes to their frontend metadata
export const WORKFLOW_META: Record<string, WorkflowMeta> = {
  landfill_mgmt: {
    code: 'landfill_mgmt',
    icon: 'Truck',
    color: 'bg-emerald-500',
    href: '/landfill', // Opens workflow dashboard
    links: [
      { labelKey: 'dashboard', href: '/landfill', icon: 'LayoutDashboard' },
      { labelKey: 'documents', href: '/landfill/documents', icon: 'FileText' },
      { labelKey: 'weighSlips', href: '/landfill/weigh-slips', icon: 'Scale' },
      { labelKey: 'hazardousSlips', href: '/landfill/hazardous-slips', icon: 'AlertTriangle' },
      { labelKey: 'sites', href: '/landfill/sites', icon: 'Building2' },
      { labelKey: 'companies', href: '/landfill/companies', icon: 'Briefcase' },
      { labelKey: 'locations', href: '/landfill/locations', icon: 'MapPin' },
      { labelKey: 'materials', href: '/landfill/materials', icon: 'Boxes' },
      { labelKey: 'export', href: '/landfill/export', icon: 'Download' },
    ],
  },
  employee_hours: {
    code: 'employee_hours',
    icon: 'Clock',
    color: 'bg-blue-500',
    href: '/employee-hours', // Future workflow
    links: [],
  },
  incoming_invoices: {
    code: 'incoming_invoices',
    icon: 'Receipt',
    color: 'bg-amber-500',
    href: '/invoices', // Future workflow
    links: [],
  },
};

// API Functions
export const workflowsApi = {
  list: async (activeOnly: boolean = true) => {
    const response = await api.get<ApiResponse<Workflow[]>>('/workflows', {
      params: { active_only: activeOnly },
    });
    return response.data;
  },

  get: async (workflowCode: string) => {
    const response = await api.get<ApiResponse<Workflow>>(`/workflows/${workflowCode}`);
    return response.data;
  },
};

// React Query Hooks
export function useWorkflows(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['workflows', { activeOnly }],
    queryFn: () => workflowsApi.list(activeOnly),
    select: (response) => response.data,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useWorkflow(workflowCode: string) {
  return useQuery({
    queryKey: ['workflow', workflowCode],
    queryFn: () => workflowsApi.get(workflowCode),
    select: (response) => response.data,
    enabled: !!workflowCode,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Helper to get workflow with its metadata
export function getWorkflowWithMeta(workflow: Workflow): Workflow & { meta: WorkflowMeta } {
  const meta = WORKFLOW_META[workflow.workflow_code] || {
    code: workflow.workflow_code,
    icon: 'Box',
    color: 'bg-gray-500',
    href: `/workflows/${workflow.workflow_code}`,
    links: [],
  };
  return { ...workflow, meta };
}
