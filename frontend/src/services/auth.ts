import api, { setTokens, clearTokens, isAuthenticated, getRefreshToken } from '@/lib/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { t } from '@/lib/translations';
import type { User, Tokens, LoginCredentials, RegisterData, TwoFactorSetup } from '@/types';
import type { ApiResponse } from '@/types/api';

// API Functions
export const authApi = {
  login: async (credentials: LoginCredentials) => {
    const response = await api.post<ApiResponse<{ user: User; tokens: Tokens; requires_2fa?: boolean; temp_token?: string }>>(
      '/auth/login',
      credentials
    );
    return response.data;
  },

  register: async (data: RegisterData) => {
    const response = await api.post<ApiResponse<{ user: User; message: string }>>('/auth/register', data);
    return response.data;
  },

  logout: async () => {
    const refreshToken = getRefreshToken();
    const response = await api.post<ApiResponse<null>>('/auth/logout', {
      refresh_token: refreshToken || '',
    });
    return response.data;
  },

  getCurrentUser: async () => {
    // API returns user fields directly in data, not nested under data.user
    const response = await api.get<ApiResponse<User>>('/auth/me');
    return response.data;
  },

  forgotPassword: async (email: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>('/auth/forgot-password', { email });
    return response.data;
  },

  resetPassword: async (data: { token: string; new_password: string }) => {
    const response = await api.post<ApiResponse<{ message: string }>>('/auth/reset-password', data);
    return response.data;
  },

  verifyEmail: async (token: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>('/auth/verify-email', { token });
    return response.data;
  },

  resendVerification: async (email: string) => {
    const response = await api.post<ApiResponse<{ message: string }>>('/auth/resend-verification', { email });
    return response.data;
  },

  // 2FA endpoints
  verify2FA: async (data: { temp_token: string; code: string }) => {
    const response = await api.post<ApiResponse<{ user: User; tokens: Tokens }>>('/auth/login/2fa', data);
    return response.data;
  },

  setup2FA: async () => {
    const response = await api.post<ApiResponse<TwoFactorSetup>>('/auth/2fa/setup');
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

  verifyBackupCode: async (data: { temp_token: string; backup_code: string }) => {
    const response = await api.post<ApiResponse<{ user: User; tokens: Tokens }>>('/auth/2fa/backup-verify', data);
    return response.data;
  },

  changePassword: async (data: { current_password: string; new_password: string }) => {
    const response = await api.post<ApiResponse<{ message: string }>>('/auth/change-password', data);
    return response.data;
  },
};

// Query Keys
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
};

// Hooks
export function useCurrentUser() {
  // Track if we're mounted (client-side)
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isAuth = mounted ? isAuthenticated() : false;

  return useQuery({
    queryKey: authKeys.user(),
    queryFn: async () => {
      const response = await authApi.getCurrentUser();
      // API returns user fields directly in response.data, not nested under response.data.user
      if (!response.data?.user_id) {
        throw new Error('No user data returned');
      }
      return response.data as unknown as User;
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: mounted && isAuth,
  });
}

export function useLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (response) => {
      if (response.data.requires_2fa) {
        // Store temp token and redirect to 2FA page
        sessionStorage.setItem('temp_token', response.data.temp_token || '');
        router.push('/2fa-verify');
      } else {
        // Store tokens and redirect to dashboard
        const { tokens, user } = response.data;
        setTokens(tokens.access_token, tokens.refresh_token);
        queryClient.setQueryData(authKeys.user(), user);
        toast.success(t.toast.loginSuccess);
        router.push('/dashboard');
      }
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.loginFailed;
      toast.error(message);
    },
  });
}

export function useRegister() {
  const router = useRouter();

  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (response) => {
      toast.success(response.data.message || t.toast.registerSuccess);
      router.push('/login');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.registerFailed;
      toast.error(message);
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      clearTokens();
      queryClient.clear();
      toast.success(t.toast.logoutSuccess);
      router.push('/login');
    },
    onError: () => {
      // Even if logout fails on server, clear local state
      clearTokens();
      queryClient.clear();
      router.push('/login');
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: authApi.forgotPassword,
    onSuccess: (response) => {
      toast.success(response.data.message || t.toast.passwordResetSent);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.passwordResetFailed;
      toast.error(message);
    },
  });
}

export function useResetPassword() {
  const router = useRouter();

  return useMutation({
    mutationFn: authApi.resetPassword,
    onSuccess: (response) => {
      toast.success(response.data.message || t.toast.passwordResetSuccess);
      router.push('/login');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.passwordResetExpired;
      toast.error(message);
    },
  });
}

export function useVerifyEmail() {
  const router = useRouter();

  return useMutation({
    mutationFn: authApi.verifyEmail,
    onSuccess: (response) => {
      toast.success(response.data.message || t.toast.emailVerified);
      router.push('/login');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.emailVerificationFailed;
      toast.error(message);
    },
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: authApi.resendVerification,
    onSuccess: (response) => {
      toast.success(response.data.message || t.toast.verificationEmailSent);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.verificationEmailFailed;
      toast.error(message);
    },
  });
}

export function useVerify2FA() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.verify2FA,
    onSuccess: (response) => {
      const { tokens, user } = response.data;
      setTokens(tokens.access_token, tokens.refresh_token);
      queryClient.setQueryData(authKeys.user(), user);
      sessionStorage.removeItem('temp_token');
      toast.success(t.toast.twoFactorVerified);
      router.push('/dashboard');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.twoFactorFailed;
      toast.error(message);
    },
  });
}

export function useVerifyBackupCode() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.verifyBackupCode,
    onSuccess: (response) => {
      const { tokens, user } = response.data;
      setTokens(tokens.access_token, tokens.refresh_token);
      queryClient.setQueryData(authKeys.user(), user);
      sessionStorage.removeItem('temp_token');
      toast.success(t.toast.backupCodeVerified);
      router.push('/dashboard');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.backupCodeFailed;
      toast.error(message);
    },
  });
}

export function useSetup2FA() {
  return useMutation({
    mutationFn: authApi.setup2FA,
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.genericError;
      toast.error(message);
    },
  });
}

export function useEnable2FA() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.enable2FA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.user() });
      toast.success(t.toast.twoFactorEnabled);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.genericError;
      toast.error(message);
    },
  });
}

export function useDisable2FA() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.disable2FA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.user() });
      toast.success(t.toast.twoFactorDisabled);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || t.toast.genericError;
      toast.error(message);
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: (response) => {
      toast.success(response.data.message || t.toast.passwordChanged);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error?.message || error.response?.data?.detail || t.toast.passwordChangeFailed;
      toast.error(message);
    },
  });
}
