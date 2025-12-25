'use client';

import { Users } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PageHeader } from '@/components/layout';
import { useRoles } from '@/services/admin';
import { t } from '@/lib/translations';

export default function RolesPage() {
  const { data: roles, isLoading } = useRoles();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t.admin.roles.title} description={t.admin.roles.subtitle} />
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
      <PageHeader title={t.admin.roles.title} description={t.admin.roles.subtitle} />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t.admin.roles.title}</CardTitle>
        </CardHeader>
        <CardContent>
          {roles && roles.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t.admin.roles.columns.name}</TableHead>
                    <TableHead>{t.admin.roles.columns.code}</TableHead>
                    <TableHead>{t.admin.roles.columns.description}</TableHead>
                    <TableHead className="text-right">{t.admin.roles.columns.userCount}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roles.map((role) => (
                    <TableRow key={role.role_id}>
                      <TableCell className="font-medium">{role.role_name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">
                          {role.role_code}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {role.description || '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          <span>{role.user_count || 0}</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-12 text-center text-muted-foreground">
              {t.admin.roles.noRoles}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
