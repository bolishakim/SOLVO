// User Types

export interface User {
  user_id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  is_active: boolean;
  is_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  last_login_at?: string;
  roles: string[];
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  user: User;
  tokens: Tokens;
  session_id: number;
}

export interface TwoFactorRequiredResponse {
  requires_2fa: true;
  temp_token: string;
}

export interface Session {
  session_id: number;
  ip_address: string;
  user_agent: string;
  created_at: string;
  expires_at: string;
  last_activity_at?: string;
}

export interface TwoFactorStatus {
  is_enabled: boolean;
  is_verified: boolean;
  backup_codes_remaining: number;
  enabled_at?: string;
  last_used_at?: string;
}

export interface TwoFactorSetupResponse {
  secret: string;
  qr_code_uri: string;
  manual_entry_key: string;
}

// Login History
export interface LoginHistoryEntry {
  log_id: number;
  user_id: number | null;
  username?: string;
  action_type: 'LOGIN' | 'LOGIN_FAILED' | 'LOGOUT';
  ip_address: string;
  user_agent: string;
  created_at: string;
  description?: string;
  changes?: {
    attempted_username?: string;
    failed_reason?: string;
    [key: string]: unknown;
  };
}

// Admin User Type (includes more fields)
export interface AdminUser extends User {
  failed_login_attempts: number;
  locked_until?: string;
  updated_at: string;
}

export interface Role {
  role_id: number;
  role_name: string;
  role_code: string;
  description?: string;
  user_count?: number;
}

// Auth Request Types
export interface LoginCredentials {
  username_or_email: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
}

export interface TwoFactorSetup {
  secret: string;
  qr_code_uri: string;
  manual_entry_key: string;
}
