import api from '@/lib/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { t } from '@/lib/translations';
import type { User, Session, LoginHistoryEntry, TwoFactorSetupResponse, TwoFactorStatus } from '@/types';
import type { ApiResponse, PaginatedResponse } from '@/types/api';

// Profile Update Data
interface UpdateProfileData {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
}

// API Functions
export const profileApi = {
  // Profile
  getProfile: async () => {
    const response = await api.get<ApiResponse<{ user: User }>>('/auth/me');
    return response.data;
  },

  updateProfile: async (data: UpdateProfileData) => {
    const response = await api.put<ApiResponse<{ user: User }>>('/auth/me', data);
    return response.data;
  },

  // Sessions
  getSessions: async () => {
    const response = await api.get<ApiResponse<{ sessions: Session[]; current_session_id: number }>>('/auth/sessions');
    return response.data;
  },

  revokeSession: async (sessionId: number) => {
    const response = await api.delete<ApiResponse<{ message: string }>>(`/auth/sessions/${sessionId}`);
    return response.data;
  },

  revokeAllSessions: async (keepCurrent: boolean = false) => {
    const response = await api.post<ApiResponse<{ message: string; revoked_count: number }>>('/auth/sessions/revoke-all', {
      keep_current: keepCurrent,
    });
    return response.data;
  },

  // Login History
  getLoginHistory: async (params?: { status?: string; limit?: number; offset?: number }) => {
    const response = await api.get<ApiResponse<PaginatedResponse<LoginHistoryEntry>>>('/auth/login-history', { params });
    return response.data;
  },

  // 2FA
  get2FAStatus: async () => {
    const response = await api.get<ApiResponse<TwoFactorStatus>>('/auth/2fa/status');
    return response.data;
  },

  setup2FA: async () => {
    const response = await api.post<ApiResponse<TwoFactorSetupResponse>>('/auth/2fa/setup');
    return response.data;
  },

  enable2FA: async (code: string) => {
    const response = await api.post<ApiResponse<{ backup_codes: string[] }>>('/auth/2fa/verify', { code });
    return response.data;
  },

  disable2FA: async (data: { code: string; password: string }) => {
    const response = await api.post<ApiResponse<{ message: string }>>('/auth/2fa/disable', data);
    return response.data;
  },

  regenerateBackupCodes: async () => {
    const response = await api.post<ApiResponse<{ backup_codes: string[] }>>('/auth/2fa/backup-codes/regenerate');
    return response.data;
  },
};

// Query Keys
export const profileKeys = {
  all: ['profile'] as const,
  user: () => [...profileKeys.all, 'user'] as const,
  sessions: () => [...profileKeys.all, 'sessions'] as const,
  loginHistory: (filters?: { status?: string }) => [...profileKeys.all, 'loginHistory', filters] as const,
  twoFactorStatus: () => [...profileKeys.all, '2fa-status'] as const,
};

// Hooks

// Profile Hooks
export function useProfile() {
  return useQuery({
    queryKey: profileKeys.user(),
    queryFn: async () => {
      const response = await profileApi.getProfile();
      // API returns user fields directly in response.data, not nested under response.data.user
      const userData = response.data?.user || response.data;
      if (!userData?.user_id) {
        throw new Error('No user data returned');
      }
      return userData as User;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileApi.updateProfile,
    onSuccess: (response) => {
      // API returns user fields directly in response.data, not nested under response.data.user
      const userData = response.data?.user || response.data;
      queryClient.setQueryData(profileKeys.user(), userData);
      queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
      toast.success(t.toast.profileUpdated);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.profileUpdateFailed;
      toast.error(message);
    },
  });
}

// Session Hooks
export function useSessions() {
  return useQuery({
    queryKey: profileKeys.sessions(),
    queryFn: async () => {
      const response = await profileApi.getSessions();
      return response.data;
    },
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileApi.revokeSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.sessions() });
      toast.success(t.toast.sessionRevoked);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.sessionRevokeFailed;
      toast.error(message);
    },
  });
}

export function useRevokeAllSessions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileApi.revokeAllSessions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.sessions() });
      toast.success(t.toast.sessionRevoked);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.sessionRevokeFailed;
      toast.error(message);
    },
  });
}

// Login History Hook
export function useLoginHistory(filters?: { status?: string; limit?: number }) {
  return useQuery({
    queryKey: profileKeys.loginHistory(filters),
    queryFn: async () => {
      const response = await profileApi.getLoginHistory(filters);
      return response.data;
    },
  });
}

// 2FA Hooks
export function use2FAStatus() {
  return useQuery({
    queryKey: profileKeys.twoFactorStatus(),
    queryFn: async () => {
      const response = await profileApi.get2FAStatus();
      return response.data;
    },
  });
}

export function useSetup2FA() {
  return useMutation({
    mutationFn: profileApi.setup2FA,
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.genericError;
      toast.error(message);
    },
  });
}

export function useEnable2FA() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileApi.enable2FA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.twoFactorStatus() });
      queryClient.invalidateQueries({ queryKey: profileKeys.user() });
      queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
      toast.success(t.toast.twoFactorEnabled);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.twoFactorFailed;
      toast.error(message);
    },
  });
}

export function useDisable2FA() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileApi.disable2FA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.twoFactorStatus() });
      queryClient.invalidateQueries({ queryKey: profileKeys.user() });
      queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
      toast.success(t.toast.twoFactorDisabled);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error?.message || error.response?.data?.detail || t.toast.twoFactorFailed;
      toast.error(message);
    },
  });
}

export function useRegenerateBackupCodes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileApi.regenerateBackupCodes,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.twoFactorStatus() });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.genericError;
      toast.error(message);
    },
  });
}
