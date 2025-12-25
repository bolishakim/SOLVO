// Audit Log Types

export type ActionType =
  | 'LOGIN'
  | 'LOGIN_FAILED'
  | 'LOGOUT'
  | 'CREATE'
  | 'UPDATE'
  | 'DELETE'
  | 'PASSWORD_CHANGE'
  | 'PASSWORD_RESET_REQUEST'
  | 'PASSWORD_RESET'
  | '2FA_ENABLED'
  | '2FA_DISABLED'
  | 'SESSION_REVOKED'
  | 'ROLE_ASSIGNED'
  | 'ROLE_REMOVED';

export type EntityType =
  | 'USER'
  | 'ROLE'
  | 'SESSION'
  | 'WEIGH_SLIP'
  | 'HAZARDOUS_SLIP'
  | 'DOCUMENT'
  | 'CONSTRUCTION_SITE'
  | 'COMPANY'
  | 'LOCATION'
  | 'MATERIAL_TYPE'
  | 'DATA_EXPORT';

export interface AuditLog {
  log_id: number;
  user_id: number;
  username?: string;
  workflow_schema?: string;
  action_type: ActionType;
  entity_type: EntityType;
  entity_id?: string;
  changes?: Record<string, unknown>;
  description?: string;
  ip_address?: string;
  user_agent?: string;
  request_id?: string;
  created_at: string;
}

export interface AuditLogFilters {
  page?: number;
  page_size?: number;
  user_id?: number;
  action_type?: ActionType;
  entity_type?: EntityType;
  entity_id?: string;
  from_date?: string;
  to_date?: string;
  ip_address?: string;
}

export interface AuditStats {
  total_logs: number;
  by_action_type: Record<string, number>;
  by_entity_type: Record<string, number>;
  recent_24h: number;
  failed_logins_24h: number;
}
