import api from '@/lib/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { t } from '@/lib/translations';
import type { AdminUser, Role, AuditLog, AuditLogFilters, AuditStats, LoginHistoryEntry } from '@/types';
import type { ApiResponse, PaginatedResponse } from '@/types/api';

// User Filters
interface UserFilters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  is_verified?: boolean;
  two_factor_enabled?: boolean;
  is_locked?: boolean;
  role?: string;
}

// Create User Data
interface CreateUserData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  is_active?: boolean;
  is_verified?: boolean;
  role_ids?: number[];
}

// Update User Data
interface UpdateUserData {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  is_active?: boolean;
}

// Admin Login History Filters
interface AdminLoginHistoryFilters {
  page?: number;
  page_size?: number;
  user_id?: number;
  status?: string;
  from_date?: string;
  to_date?: string;
  ip_address?: string;
}

// Security Dashboard Stats
interface SecurityStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  users_with_2fa: number;
  users_without_2fa: number;
  locked_accounts: number;
  failed_logins_24h: number;
  unverified_users: number;
  two_factor_adoption_rate: number;
  inactive_accounts: number;
  suspicious_activities: number;
}

interface LockedAccount {
  user_id: number;
  username: string;
  email: string;
  failed_login_attempts: number;
  locked_until: string;
  last_failed_at?: string;
}

// API Functions
export const adminApi = {
  // Users
  getUsers: async (filters?: UserFilters) => {
    const response = await api.get<PaginatedResponse<AdminUser>>('/admin/users', { params: filters });
    return response.data;
  },

  getUser: async (userId: string) => {
    const response = await api.get<ApiResponse<{ user: AdminUser }>>(`/admin/users/${userId}`);
    return response.data;
  },

  createUser: async (data: CreateUserData) => {
    const response = await api.post<ApiResponse<{ user: AdminUser }>>('/admin/users', data);
    return response.data;
  },

  updateUser: async (userId: string, data: UpdateUserData) => {
    const response = await api.put<ApiResponse<{ user: AdminUser }>>(`/admin/users/${userId}`, data);
    return response.data;
  },

  unlockUser: async (userId: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/unlock`);
    return response.data;
  },

  deactivateUser: async (userId: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/deactivate`);
    return response.data;
  },

  activateUser: async (userId: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/activate`);
    return response.data;
  },

  reset2FA: async (userId: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/disable-2fa`);
    return response.data;
  },

  resetPassword: async (userId: string, newPassword: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/reset-password`, {
      new_password: newPassword,
    });
    return response.data;
  },

  sendPasswordReset: async (userId: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/send-password-reset`);
    return response.data;
  },

  forceLogout: async (userId: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/force-logout`);
    return response.data;
  },

  // User Roles
  assignRole: async (userId: string, roleCode: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>(`/admin/users/${userId}/roles`, { role_code: roleCode });
    return response.data;
  },

  removeRole: async (userId: string, roleCode: string) => {
    const response = await api.delete<ApiResponse<{ message: string }>>(`/admin/users/${userId}/roles/${roleCode}`);
    return response.data;
  },

  // Roles
  getRoles: async () => {
    const response = await api.get<ApiResponse<{ roles: Role[] }>>('/admin/roles');
    return response.data;
  },

  // Audit Logs
  getAuditLogs: async (filters?: AuditLogFilters) => {
    const response = await api.get<PaginatedResponse<AuditLog>>('/admin/audit-logs', { params: filters });
    return response.data;
  },

  getAuditStats: async () => {
    const response = await api.get<ApiResponse<AuditStats>>('/admin/audit-logs/stats');
    return response.data;
  },

  // Admin Login History
  getLoginHistory: async (filters?: AdminLoginHistoryFilters) => {
    const response = await api.get<PaginatedResponse<LoginHistoryEntry>>('/admin/login-history', { params: filters });
    return response.data;
  },

  exportLoginHistory: async (filters?: AdminLoginHistoryFilters) => {
    const response = await api.get('/admin/login-history/export', {
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  },

  // Security Dashboard
  getSecurityStats: async () => {
    const response = await api.get<ApiResponse<SecurityStats>>('/admin/security/stats');
    return response.data;
  },

  getLockedAccounts: async () => {
    const response = await api.get<ApiResponse<{ accounts: LockedAccount[] }>>('/admin/security/locked-accounts');
    return response.data;
  },

  getFailedLogins: async (hours: number = 24) => {
    const response = await api.get<ApiResponse<{ logins: LoginHistoryEntry[] }>>('/admin/security/failed-logins', {
      params: { hours }
    });
    return response.data;
  },

  getUsersWithout2FA: async () => {
    const response = await api.get<ApiResponse<{ users: AdminUser[] }>>('/admin/security/users-without-2fa');
    return response.data;
  },
};

// Query Keys
export const adminKeys = {
  all: ['admin'] as const,
  users: (filters?: UserFilters) => [...adminKeys.all, 'users', filters] as const,
  user: (id: string) => [...adminKeys.all, 'user', id] as const,
  roles: () => [...adminKeys.all, 'roles'] as const,
  auditLogs: (filters?: AuditLogFilters) => [...adminKeys.all, 'auditLogs', filters] as const,
  auditStats: () => [...adminKeys.all, 'auditStats'] as const,
  loginHistory: (filters?: AdminLoginHistoryFilters) => [...adminKeys.all, 'loginHistory', filters] as const,
  securityStats: () => [...adminKeys.all, 'securityStats'] as const,
  lockedAccounts: () => [...adminKeys.all, 'lockedAccounts'] as const,
  failedLogins: (hours?: number) => [...adminKeys.all, 'failedLogins', hours] as const,
  usersWithout2FA: () => [...adminKeys.all, 'usersWithout2FA'] as const,
};

// Hooks

// User Hooks
export function useUsers(filters?: UserFilters) {
  return useQuery({
    queryKey: adminKeys.users(filters),
    queryFn: () => adminApi.getUsers(filters),
  });
}

export function useUser(userId: string) {
  return useQuery({
    queryKey: adminKeys.user(userId),
    queryFn: () => adminApi.getUser(userId),
    enabled: !!userId,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: adminApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      toast.success(t.admin.userCreated);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.userCreateFailed;
      toast.error(message);
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UpdateUserData }) =>
      adminApi.updateUser(userId, data),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      toast.success(t.admin.userUpdated);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.userUpdateFailed;
      toast.error(message);
    },
  });
}

export function useUnlockUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: adminApi.unlockUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminKeys.lockedAccounts() });
      queryClient.invalidateQueries({ queryKey: adminKeys.securityStats() });
      toast.success(t.admin.userUnlocked);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.userUnlockFailed;
      toast.error(message);
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: adminApi.deactivateUser,
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      toast.success(t.admin.userDeactivated);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.userDeactivateFailed;
      toast.error(message);
    },
  });
}

export function useActivateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: adminApi.activateUser,
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      toast.success(t.admin.userActivated);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.userActivateFailed;
      toast.error(message);
    },
  });
}

export function useReset2FA() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: adminApi.reset2FA,
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      toast.success(t.admin.twoFactorReset);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.twoFactorResetFailed;
      toast.error(message);
    },
  });
}

export function useResetPassword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, newPassword }: { userId: string; newPassword: string }) =>
      adminApi.resetPassword(userId, newPassword),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      toast.success(t.admin.passwordResetSuccess || 'Passwort erfolgreich zurückgesetzt');
    },
    onError: (error: any) => {
      const message = error.response?.data?.error?.message || error.response?.data?.detail || t.admin.passwordResetFailed;
      toast.error(message);
    },
  });
}

export function useSendPasswordReset() {
  return useMutation({
    mutationFn: adminApi.sendPasswordReset,
    onSuccess: () => {
      toast.success(t.admin.passwordResetSent);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.passwordResetFailed;
      toast.error(message);
    },
  });
}

export function useForceLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: adminApi.forceLogout,
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      toast.success(t.admin.userLoggedOut);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.userLogoutFailed;
      toast.error(message);
    },
  });
}

// Role Hooks
export function useRoles() {
  return useQuery({
    queryKey: adminKeys.roles(),
    queryFn: async () => {
      const response = await adminApi.getRoles();
      // API returns { success: true, data: [...roles] }
      const roles = response.data?.roles || response.data;
      if (!roles) {
        return [];
      }
      return Array.isArray(roles) ? roles : [];
    },
  });
}

export function useAssignRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, roleCode }: { userId: string; roleCode: string }) =>
      adminApi.assignRole(userId, roleCode),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminKeys.roles() });
      toast.success(t.admin.roleAssigned);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.roleAssignFailed;
      toast.error(message);
    },
  });
}

export function useRemoveRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, roleCode }: { userId: string; roleCode: string }) =>
      adminApi.removeRole(userId, roleCode),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminKeys.roles() });
      toast.success(t.admin.roleRemoved);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.admin.roleRemoveFailed;
      toast.error(message);
    },
  });
}

// Audit Log Hooks
export function useAuditLogs(filters?: AuditLogFilters) {
  return useQuery({
    queryKey: adminKeys.auditLogs(filters),
    queryFn: () => adminApi.getAuditLogs(filters),
  });
}

export function useAuditStats() {
  return useQuery({
    queryKey: adminKeys.auditStats(),
    queryFn: async () => {
      const response = await adminApi.getAuditStats();
      return response.data;
    },
  });
}

// Admin Login History Hooks
export function useAdminLoginHistory(filters?: AdminLoginHistoryFilters) {
  return useQuery({
    queryKey: adminKeys.loginHistory(filters),
    queryFn: () => adminApi.getLoginHistory(filters),
  });
}

// Security Dashboard Hooks
export function useSecurityStats() {
  return useQuery({
    queryKey: adminKeys.securityStats(),
    queryFn: async () => {
      const response = await adminApi.getSecurityStats();
      return response.data || {};
    },
  });
}

export function useLockedAccounts() {
  return useQuery({
    queryKey: adminKeys.lockedAccounts(),
    queryFn: async () => {
      const response = await adminApi.getLockedAccounts();
      return response.data?.accounts || [];
    },
  });
}

export function useFailedLogins(hours: number = 24) {
  return useQuery({
    queryKey: adminKeys.failedLogins(hours),
    queryFn: async () => {
      const response = await adminApi.getFailedLogins(hours);
      // Backend returns 'logs' not 'logins'
      return response.data?.logs || response.data?.logins || [];
    },
  });
}

export function useUsersWithout2FA() {
  return useQuery({
    queryKey: adminKeys.usersWithout2FA(),
    queryFn: async () => {
      const response = await adminApi.getUsersWithout2FA();
      return response.data?.users || [];
    },
  });
}
