'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Filter,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Globe,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { PageHeader } from '@/components/layout';
import { useAuditLogs } from '@/services/admin';
import { t } from '@/lib/translations';
import type { AuditLog, ActionType, EntityType } from '@/types/audit';

const actionTypes: ActionType[] = [
  'LOGIN', 'LOGIN_FAILED', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE',
  'PASSWORD_CHANGE', 'PASSWORD_RESET_REQUEST', 'PASSWORD_RESET',
  '2FA_ENABLED', '2FA_DISABLED', 'SESSION_REVOKED', 'ROLE_ASSIGNED', 'ROLE_REMOVED'
];

const entityTypes: EntityType[] = [
  'USER', 'ROLE', 'SESSION', 'WEIGH_SLIP', 'HAZARDOUS_SLIP', 'DOCUMENT',
  'CONSTRUCTION_SITE', 'COMPANY', 'LOCATION', 'MATERIAL_TYPE', 'DATA_EXPORT'
];

function ActionBadge({ action }: { action: ActionType }) {
  const variant = action.includes('FAILED') || action === 'DELETE' ? 'destructive' :
                  action === 'LOGIN' || action === 'CREATE' ? 'default' : 'secondary';

  const label = t.admin.auditLogs.actions[action] || action;

  return <Badge variant={variant}>{label}</Badge>;
}

function EntityBadge({ entity }: { entity: EntityType }) {
  const label = t.admin.auditLogs.entities[entity] || entity;
  return <Badge variant="outline">{label}</Badge>;
}

function AuditLogRow({ log }: { log: AuditLog }) {
  const [isOpen, setIsOpen] = useState(false);
  const hasDetails = log.changes || log.description;

  return (
    <>
      <TableRow>
        <TableCell>
          <div className="space-y-1">
            <p className="font-medium">
              {format(new Date(log.created_at), 'dd.MM.yyyy', { locale: de })}
            </p>
            <p className="text-xs text-muted-foreground">
              {format(new Date(log.created_at), 'HH:mm:ss', { locale: de })}
            </p>
          </div>
        </TableCell>
        <TableCell>
          <span className="font-medium">{log.username || `User #${log.user_id}`}</span>
        </TableCell>
        <TableCell>
          <ActionBadge action={log.action_type} />
        </TableCell>
        <TableCell>
          <EntityBadge entity={log.entity_type} />
        </TableCell>
        <TableCell className="font-mono text-sm">
          {log.entity_id || '-'}
        </TableCell>
        <TableCell>
          {log.ip_address && (
            <div className="flex items-center gap-1 text-sm">
              <Globe className="h-3 w-3" />
              {log.ip_address}
            </div>
          )}
        </TableCell>
        <TableCell>
          {hasDetails && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(!isOpen)}
            >
              {isOpen ? (
                <>
                  <ChevronUp className="mr-1 h-4 w-4" />
                  {t.admin.auditLogs.collapseDetails}
                </>
              ) : (
                <>
                  <ChevronDown className="mr-1 h-4 w-4" />
                  {t.admin.auditLogs.expandDetails}
                </>
              )}
            </Button>
          )}
        </TableCell>
      </TableRow>
      {hasDetails && isOpen && (
        <TableRow>
          <TableCell colSpan={7} className="bg-muted/50">
            <div className="p-4 space-y-2">
              {log.description && (
                <p className="text-sm">{log.description}</p>
              )}
              {log.changes && (
                <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
                  {JSON.stringify(log.changes, null, 2)}
                </pre>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

export default function AuditLogsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<{
    action_type?: ActionType;
    entity_type?: EntityType;
    from_date?: string;
    to_date?: string;
  }>({});

  const { data: logsData, isLoading } = useAuditLogs({
    page,
    page_size: 20,
    ...filters,
  });

  const logs = logsData?.data || [];
  const pagination = logsData?.pagination;

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const hasActiveFilters = Object.keys(filters).length > 0;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.admin.auditLogs.title} description={t.admin.auditLogs.subtitle} />
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t.admin.auditLogs.title} description={t.admin.auditLogs.subtitle} />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t.admin.auditLogs.title}</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="mb-4 flex flex-wrap items-end gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
            </div>

            <div className="space-y-1">
              <Label className="text-xs">{t.admin.auditLogs.filters.action}</Label>
              <Select
                value={filters.action_type || 'all'}
                onValueChange={(value) => {
                  setFilters((prev) => ({
                    ...prev,
                    action_type: value === 'all' ? undefined : value as ActionType,
                  }));
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.common.all}</SelectItem>
                  {actionTypes.map((action) => (
                    <SelectItem key={action} value={action}>
                      {t.admin.auditLogs.actions[action] || action}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label className="text-xs">{t.admin.auditLogs.filters.entity}</Label>
              <Select
                value={filters.entity_type || 'all'}
                onValueChange={(value) => {
                  setFilters((prev) => ({
                    ...prev,
                    entity_type: value === 'all' ? undefined : value as EntityType,
                  }));
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.common.all}</SelectItem>
                  {entityTypes.map((entity) => (
                    <SelectItem key={entity} value={entity}>
                      {t.admin.auditLogs.entities[entity] || entity}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label className="text-xs">{t.admin.auditLogs.filters.from}</Label>
              <Input
                type="date"
                className="w-40"
                value={filters.from_date || ''}
                onChange={(e) => {
                  setFilters((prev) => ({
                    ...prev,
                    from_date: e.target.value || undefined,
                  }));
                  setPage(1);
                }}
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs">{t.admin.auditLogs.filters.to}</Label>
              <Input
                type="date"
                className="w-40"
                value={filters.to_date || ''}
                onChange={(e) => {
                  setFilters((prev) => ({
                    ...prev,
                    to_date: e.target.value || undefined,
                  }));
                  setPage(1);
                }}
              />
            </div>

            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                {t.admin.auditLogs.filters.clearFilters}
              </Button>
            )}
          </div>

          {/* Table */}
          {logs.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[100px]">{t.admin.auditLogs.columns.timestamp}</TableHead>
                      <TableHead>{t.admin.auditLogs.columns.user}</TableHead>
                      <TableHead>{t.admin.auditLogs.columns.action}</TableHead>
                      <TableHead>{t.admin.auditLogs.columns.entity}</TableHead>
                      <TableHead>{t.admin.auditLogs.columns.entityId}</TableHead>
                      <TableHead>{t.admin.auditLogs.columns.ipAddress}</TableHead>
                      <TableHead>{t.admin.auditLogs.columns.details}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => (
                      <AuditLogRow key={log.log_id} log={log} />
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {pagination && pagination.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Seite {pagination.page} von {pagination.total_pages} ({pagination.total_items} Einträge)
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                      disabled={page === pagination.total_pages}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="py-12 text-center text-muted-foreground">
              {t.admin.auditLogs.noLogs}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
