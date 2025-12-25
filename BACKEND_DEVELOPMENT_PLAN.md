# Landfill Management System - Backend Development Plan

## Core App Development Roadmap

**Tech Stack**: Python 3.11+ | FastAPI | SQLAlchemy | PostgreSQL | JWT + TOTP

**Architecture**: Modular workflow-based structure for long-term extensibility

---

## Project Architecture

### Design Principles
- **Core/Workflow Separation**: Core app handles auth, users, audit - workflows are independent modules
- **Schema Alignment**: Folder structure mirrors database schema structure
- **Extensibility**: Adding a new workflow = adding a new folder under `workflows/`
- **Isolation**: Each workflow is self-contained with its own models, schemas, routers, services

### Folder Structure

```
SOLVO/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry, mounts workflow routers
│   ├── config.py                    # Global configuration
│   ├── database.py                  # DB connection, session management
│   │
│   ├── core/                        # ═══ CORE APPLICATION ═══
│   │   ├── __init__.py              # (auth, users, audit, sessions)
│   │   ├── dependencies.py          # get_current_user, require_role, etc.
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # User model
│   │   │   ├── role.py              # Role, UserRole models
│   │   │   ├── session.py           # UserSession model
│   │   │   ├── two_factor.py        # TwoFactorAuth model
│   │   │   ├── workflow.py          # Workflow registry model
│   │   │   ├── audit_log.py         # AuditLog model
│   │   │   └── data_export.py       # DataExport model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # User request/response schemas
│   │   │   ├── auth.py              # Login, register, token schemas
│   │   │   ├── session.py           # Session schemas
│   │   │   ├── two_factor.py        # 2FA schemas
│   │   │   └── audit.py             # Audit log schemas
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # /auth/* endpoints
│   │   │   ├── users.py             # /users/* endpoints (self-service)
│   │   │   └── admin.py             # /admin/* endpoints (admin only)
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py      # Authentication logic
│   │       ├── user_service.py      # User CRUD operations
│   │       ├── session_service.py   # Session management
│   │       ├── two_factor_service.py # TOTP generation/verification
│   │       └── audit_service.py     # Audit logging
│   │
│   ├── workflows/                   # ═══ ALL WORKFLOWS ═══
│   │   ├── __init__.py              # Workflow registry & auto-discovery
│   │   │
│   │   ├── landfill_mgmt/           # ─── Workflow 1: Landfill Management ───
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Workflow-specific configuration
│   │   │   │
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── construction_site.py
│   │   │   │   ├── user_site_access.py    # User-site assignments
│   │   │   │   ├── landfill_company.py
│   │   │   │   ├── landfill_location.py
│   │   │   │   ├── material_type.py
│   │   │   │   ├── pdf_document.py
│   │   │   │   ├── weigh_slip.py
│   │   │   │   └── hazardous_slip.py
│   │   │   │
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── construction_site.py
│   │   │   │   ├── weigh_slip.py
│   │   │   │   ├── hazardous_slip.py
│   │   │   │   ├── pdf_document.py
│   │   │   │   ├── master_data.py         # Companies, locations, materials
│   │   │   │   └── export.py
│   │   │   │
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py            # Aggregates all workflow routers
│   │   │   │   ├── documents.py           # /landfill/documents/*
│   │   │   │   ├── weigh_slips.py         # /landfill/weigh-slips/*
│   │   │   │   ├── hazardous_slips.py     # /landfill/hazardous-slips/*
│   │   │   │   ├── construction_sites.py  # /landfill/construction-sites/*
│   │   │   │   ├── master_data.py         # /landfill/companies/*, /landfill/locations/*, etc.
│   │   │   │   └── exports.py             # /landfill/export/*
│   │   │   │
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       ├── pdf_service.py         # PDF upload, storage
│   │   │       ├── extraction_service.py  # LLM integration for data extraction
│   │   │       ├── weigh_slip_service.py  # Weigh slip CRUD & assignment
│   │   │       ├── site_service.py        # Construction site management
│   │   │       ├── access_control_service.py  # User-site access logic
│   │   │       └── export_service.py      # Excel/PDF export generation
│   │   │
│   │   └── _template/               # ─── Template for New Workflows ───
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── models/
│   │       │   └── __init__.py
│   │       ├── schemas/
│   │       │   └── __init__.py
│   │       ├── routers/
│   │       │   └── __init__.py
│   │       └── services/
│   │           └── __init__.py
│   │
│   ├── shared/                      # ═══ SHARED UTILITIES ═══
│   │   ├── __init__.py
│   │   ├── base_model.py            # SQLAlchemy base with created_at, updated_at
│   │   ├── responses.py             # Standardized API response helpers
│   │   ├── pagination.py            # Pagination utilities
│   │   ├── exceptions.py            # Custom exception classes
│   │   ├── security.py              # Password hashing, JWT utilities
│   │   └── validators.py            # Common validation functions
│   │
│   └── middleware/                  # ═══ MIDDLEWARE ═══
│       ├── __init__.py
│       ├── rate_limit.py            # Rate limiting per user
│       ├── request_id.py            # X-Request-ID tracking
│       ├── security_headers.py      # Security headers injection
│       └── audit.py                 # Auto audit logging middleware
│
├── alembic/                         # ═══ DATABASE MIGRATIONS ═══
│   ├── versions/
│   │   └── .gitkeep
│   ├── env.py
│   └── script.py.mako
│
├── tests/                           # ═══ TESTS ═══
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures, test DB setup
│   │
│   ├── core/                        # Core app tests
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_sessions.py
│   │   ├── test_two_factor.py
│   │   └── test_audit.py
│   │
│   └── workflows/                   # Workflow tests
│       └── landfill_mgmt/
│           ├── __init__.py
│           ├── test_documents.py
│           ├── test_weigh_slips.py
│           ├── test_construction_sites.py
│           └── test_exports.py
│
├── scripts/                         # ═══ UTILITY SCRIPTS ═══
│   ├── seed_data.py                 # Seed default roles, workflows, sample data
│   └── create_admin.py              # Create initial admin user
│
├── requirements.txt
├── requirements-dev.txt             # Dev dependencies (pytest, etc.)
├── .env.example
├── .gitignore
├── docker-compose.yml               # PostgreSQL for local dev
├── Dockerfile                       # Production container
├── alembic.ini
└── README.md
```

### Database Schema Mapping

| Folder | PostgreSQL Schema | Purpose |
|--------|-------------------|---------|
| `app/core/` | `core_app` | Authentication, users, audit, sessions |
| `app/workflows/landfill_mgmt/` | `landfill_mgmt` | Landfill document management |
| `app/workflows/[future]/` | `[future_schema]` | Future workflows |

---

## Phase 1: Project Setup & Foundation
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Create project folder structure as defined above
- [x] Initialize `requirements.txt` with dependencies
- [x] Create `app/config.py` with Pydantic Settings
- [x] Create `.env.example` with all required variables
- [x] Set up `app/database.py` with async SQLAlchemy engine
- [x] Configure multi-schema support (core_app schema)
- [x] Create `app/shared/base_model.py` with TimestampMixin
- [x] Initialize Alembic with multi-schema env.py
- [x] Create `docker-compose.yml` for PostgreSQL
- [x] Create `app/main.py` with basic FastAPI app
- [x] Implement `/health` and `/health/db` endpoints
- [x] Create `.gitignore`

### Deliverables:
- [x] Working FastAPI app with health endpoints
- [x] Database connection established
- [x] Alembic configured for multi-schema migrations
- [x] Docker Compose ready for local development

---

## Phase 2: Database Models (Core App)
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Create `app/core/models/user.py` - User model
- [x] Create `app/core/models/role.py` - Role and UserRole models
- [x] Create `app/core/models/session.py` - UserSession model
- [x] Create `app/core/models/two_factor.py` - TwoFactorAuth model
- [x] Create `app/core/models/workflow.py` - Workflow model
- [x] Create `app/core/models/audit_log.py` - AuditLog model
- [x] Create `app/core/models/data_export.py` - DataExport model
- [x] Create `app/core/models/__init__.py` - Export all models
- [x] Generate Alembic migration for core_app schema
- [x] Create `scripts/seed_data.py` for default roles and workflow

### Deliverables:
- [x] All core_app models defined with proper relationships
- [x] Database tables created via migration
- [x] Default roles (Admin, Standard User, Viewer) seeded
- [x] Default workflow (landfill_mgmt) registered

---

## Phase 3: Shared Utilities & Response Standards
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Create `app/shared/responses.py`:
  - [x] `success_response(data, message)` helper
  - [x] `error_response(code, message, details)` helper
  - [x] `paginated_response(data, pagination)` helper
  - [x] `ErrorCodes` class with all error code constants
- [x] Create `app/shared/pagination.py`:
  - [x] `PaginationParams` dependency
  - [x] `PaginatedResult` generic class
  - [x] `paginate_query()` utility for SQLAlchemy
  - [x] `paginate_list()` utility for in-memory lists
- [x] Create `app/shared/exceptions.py`:
  - [x] `AppException` base class with `to_dict()` method
  - [x] `NotFoundException`, `UnauthorizedException`, `ForbiddenException`
  - [x] `ValidationException`, `InvalidInputException`
  - [x] `AlreadyExistsException`, `ConflictException`
  - [x] `TokenExpiredException`, `TokenInvalidException`
  - [x] `SessionExpiredException`, `SessionRevokedException`
  - [x] `TwoFactorRequiredException`, `TwoFactorInvalidException`
  - [x] `AccountLockedException`, `AccountDisabledException`
  - [x] `RateLimitExceededException`
  - [x] `DatabaseErrorException`, `ServiceUnavailableException`
- [x] Create `app/shared/security.py`:
  - [x] Password hashing with bcrypt (configurable rounds)
  - [x] Password verification
  - [x] JWT access token creation
  - [x] JWT refresh token creation
  - [x] JWT token decoding/validation
  - [x] Token ID generation (jti claim)
  - [x] Session token generation
  - [x] Password reset token generation
  - [x] Bearer token extraction from Authorization header
- [x] Create `app/shared/validators.py`:
  - [x] Email validator with RFC 5322 regex
  - [x] Password strength validator with configurable requirements
  - [x] Password strength analyzer with score and feedback
  - [x] Username format validator
  - [x] Phone number validator
  - [x] Name field validator
  - [x] Combined registration data validator
- [x] Register exception handlers in `main.py`
- [x] Update `app/shared/__init__.py` to export all utilities

### Deliverables:
- [x] Standardized response format across all endpoints
- [x] Reusable pagination with SQLAlchemy integration
- [x] Custom exceptions with proper HTTP responses
- [x] Security utilities ready for auth (password hashing, JWT)

---

## Phase 4: Authentication System
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Create `app/core/schemas/auth.py`:
  - [x] `RegisterRequest` with validation
  - [x] `LoginRequest` with username/email support
  - [x] `LoginResponse`, `RefreshTokenResponse`
  - [x] `RefreshTokenRequest`
  - [x] `PasswordChangeRequest`
  - [x] `TwoFactorLoginRequest` (prepared for Phase 6)
- [x] Create `app/core/schemas/user.py`:
  - [x] `UserResponse`, `UserWithRolesResponse`
  - [x] `UserUpdate`, `UserAdminUpdate`
  - [x] `RoleResponse`
- [x] Create `app/core/services/auth_service.py`:
  - [x] `register()` - Create new user with hashed password
  - [x] `authenticate()` - Verify credentials
  - [x] `login()` - Full login flow with 2FA support
  - [x] `create_tokens()` - Generate JWT access/refresh tokens
  - [x] `refresh_tokens()` - Refresh access token
  - [x] `change_password()` - Password change with verification
  - [x] `validate_token()` - Token validation
- [x] Create `app/core/services/user_service.py`:
  - [x] `get_by_id()`, `get_by_email()`, `get_by_username()`
  - [x] `get_by_username_or_email()` - For login flexibility
  - [x] `create()` - Create user with default role assignment
  - [x] `update()` - Update user profile
  - [x] `update_password()`, `update_last_login()`
  - [x] `get_user_roles()`, `get_user_role_codes()`, `has_role()`
- [x] Create `app/core/routers/auth.py`:
  - [x] `POST /auth/register` - User registration
  - [x] `POST /auth/login` - User login (with 2FA ready)
  - [x] `POST /auth/logout` - User logout
  - [x] `POST /auth/refresh-token` - Token refresh
  - [x] `GET /auth/session/validate` - Validate current session
  - [x] `POST /auth/change-password` - Change password
  - [x] `GET /auth/me` - Get current user profile
  - [x] `PUT /auth/me` - Update current user profile
- [x] Create `app/core/dependencies.py`:
  - [x] `get_current_user` - Extract user from JWT
  - [x] `get_current_active_user` - Verify user is active
  - [x] `require_role()` - Role-based access dependency
  - [x] `require_any_role()` - Multi-role access dependency
  - [x] `require_admin()` - Admin shortcut
  - [x] `get_optional_user` - Optional authentication
- [x] Register auth router in `main.py`
- [x] Added `is_verified` and `two_factor_enabled` fields to User model
- [x] Added `role_code` field to Role model for machine-readable identifiers

### Deliverables:
- [x] Full registration and login flow
- [x] JWT access and refresh tokens
- [x] Protected route dependencies
- [x] Role-based access control dependencies
- [x] Logout functionality
- [x] Password change functionality

---

## Phase 5: Session Management
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Create `app/core/schemas/session.py`:
  - [x] `SessionResponse` - Session info for API responses
  - [x] `SessionListResponse` - List of sessions
  - [x] `SessionRevokeResponse`, `SessionRevokeAllResponse`
  - [x] `SessionCreate` - Internal schema
- [x] Create `app/core/services/session_service.py`:
  - [x] `create_session(user_id, refresh_token_jti, ip_address, user_agent)`
  - [x] `get_by_id()`, `get_by_token()`, `get_by_refresh_token()`
  - [x] `validate_session(refresh_token_jti)`
  - [x] `get_user_sessions(user_id)`
  - [x] `get_active_session_count(user_id)`
  - [x] `update_activity(session_id)`
  - [x] `revoke_session(session_id, user_id)`
  - [x] `revoke_session_by_refresh_token(jti)`
  - [x] `revoke_all_sessions(user_id, except_session_id)`
  - [x] `cleanup_expired_sessions(older_than_days)`
- [x] Update `auth_service.py`:
  - [x] Initialize `SessionService` in constructor
  - [x] `login()` accepts `ip_address` and `user_agent`
  - [x] `_complete_login()` creates session linked to refresh token JTI
  - [x] `create_tokens()` generates unique JTI for session tracking
  - [x] `refresh_tokens()` validates session before refreshing
  - [x] `logout()` revokes session by refresh token
  - [x] `logout_all_sessions()` with option to keep current
  - [x] `get_user_sessions()`, `revoke_session()` wrapper methods
- [x] Update `dependencies.py`:
  - [x] `get_client_ip()` - Extract IP from X-Forwarded-For/X-Real-IP
  - [x] `get_user_agent()` - Extract User-Agent header
  - [x] `ClientIP`, `UserAgent` type aliases
- [x] Add session endpoints to `app/core/routers/auth.py`:
  - [x] `GET /auth/sessions` - List active sessions with IP, user agent, timestamps
  - [x] `DELETE /auth/sessions/{session_id}` - Revoke specific session
  - [x] `POST /auth/sessions/revoke-all` - Revoke all sessions (optionally keep current)
- [x] Update `POST /auth/login` to pass IP and user agent, return `session_id`
- [x] Update `POST /auth/logout` to accept `refresh_token` and revoke session
- [x] Add `LogoutRequest`, `LogoutAllRequest` schemas to `auth.py`

### Deliverables:
- [x] Sessions stored in database with refresh token JTI linkage
- [x] Session validation on token refresh (revoked sessions rejected)
- [x] View all active sessions with device info
- [x] Revoke individual sessions or all at once
- [x] IP address and user agent tracking
- [x] Session expiration aligned with refresh token expiry

---

## Phase 6: Two-Factor Authentication (2FA)
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Create `app/core/schemas/two_factor.py`:
  - [x] `TwoFactorSetupRequest`, `TwoFactorSetupResponse` (includes QR code URI)
  - [x] `TwoFactorVerifyRequest`, `TwoFactorVerifyResponse`
  - [x] `TwoFactorStatusResponse`
  - [x] `TwoFactorDisableRequest`, `TwoFactorDisableResponse`
  - [x] `TwoFactorLoginRequest` - For login step 2
  - [x] `BackupCodeVerifyRequest` - For backup code login
  - [x] `BackupCodesResponse` - For regenerating backup codes
- [x] Create `app/core/services/two_factor_service.py`:
  - [x] `initiate_setup(user)` - Generate secret and QR URI
  - [x] `verify_and_enable(user, code)` - Verify and enable with backup codes
  - [x] `disable(user, code, password_verified)` - Disable 2FA
  - [x] `verify_code(user_id, code)` - Verify TOTP code
  - [x] `verify_backup_code(user_id, backup_code)` - Verify and consume backup code
  - [x] `get_status(user_id)` - Get 2FA status
  - [x] `is_enabled(user_id)` - Check if enabled
  - [x] `regenerate_backup_codes(user, code)` - Generate new backup codes
  - [x] `_verify_totp(secret, code)` - TOTP verification with valid_window=1
  - [x] `_generate_backup_codes()` - Generate XXXX-XXXX format codes
- [x] Add 2FA endpoints to `app/core/routers/auth.py`:
  - [x] `POST /auth/2fa/setup` - Generate secret and QR URI
  - [x] `POST /auth/2fa/verify` - Verify code and enable 2FA
  - [x] `POST /auth/2fa/disable` - Disable 2FA with code verification
  - [x] `GET /auth/2fa/status` - Check 2FA status with backup code count
  - [x] `POST /auth/2fa/backup-codes/regenerate` - Regenerate backup codes
  - [x] `POST /auth/login/2fa` - Complete login with TOTP code
  - [x] `POST /auth/login/backup-code` - Complete login with backup code
- [x] Update `app/core/services/auth_service.py`:
  - [x] Initialize `TwoFactorService` in constructor
  - [x] Login returns `requires_2fa: true` with temp_token when 2FA enabled
  - [x] `verify_2fa_login(temp_token, code)` - Complete login with TOTP
  - [x] `verify_2fa_login_backup(temp_token, backup_code)` - Complete login with backup code
  - [x] `_generate_temp_token(user)` - Generate 5-minute temp token for 2FA flow

### Deliverables:
- [x] TOTP-based 2FA setup with QR code and manual entry key
- [x] Two-step login flow for 2FA users (temp_token mechanism)
- [x] Backup codes (10 codes, XXXX-XXXX format) with one-time use
- [x] Backup code regeneration with TOTP verification
- [x] Login with backup code as alternative to TOTP

---

## Phase 7: Role-Based Access Control (RBAC)
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Update `app/core/dependencies.py`:
  - [x] `require_role(role_name)` - Single role check (already existed)
  - [x] `require_any_role(role_names)` - Any of roles (already existed)
  - [x] `require_admin()` - Admin shortcut (already existed)
- [x] Create `app/core/services/role_service.py`:
  - [x] `get_user_roles(user_id)` - Get all roles for a user
  - [x] `get_user_role_codes(user_id)` - Get role codes for a user
  - [x] `assign_role(user_id, role_id, assigned_by)` - Assign role with attribution
  - [x] `assign_role_by_code(user_id, role_code, assigned_by)` - Assign by role code
  - [x] `remove_role(user_id, role_id)` - Remove role from user
  - [x] `remove_role_by_code(user_id, role_code)` - Remove by role code
  - [x] `set_user_roles(user_id, role_ids, assigned_by)` - Set exact roles
  - [x] `get_all_roles()` - List all available roles
  - [x] `get_role_by_id(role_id)`, `get_role_by_code(role_code)` - Role lookups
  - [x] `has_role(user_id, role_code)`, `is_admin(user_id)` - Role checks
  - [x] `get_role_user_count(role_id)` - Count users with role
  - [x] `get_users_with_role(role_id)` - List users with role
- [x] Create `app/core/routers/admin.py`:
  - [x] `GET /admin/users` - List all users (paginated with search/filter)
  - [x] `GET /admin/users/{user_id}` - Get user details with roles
  - [x] `PUT /admin/users/{user_id}` - Update user profile and status
  - [x] `DELETE /admin/users/{user_id}` - Deactivate user (soft delete)
  - [x] `GET /admin/users/{user_id}/roles` - Get user's roles
  - [x] `POST /admin/users/{user_id}/roles` - Assign role to user
  - [x] `DELETE /admin/users/{user_id}/roles/{role_id}` - Remove role from user
  - [x] `GET /admin/roles` - List all roles with user counts
  - [x] `GET /admin/stats` - Admin statistics (users, roles, 2FA usage)
- [x] Register admin router in `main.py` with `/admin` prefix
- [x] Update `app/core/schemas/user.py` with role management schemas:
  - [x] `RoleAssignRequest`, `RoleRemoveRequest`, `SetUserRolesRequest`
  - [x] `RoleDetailResponse`, `RolesWithCountResponse`

### Deliverables:
- [x] Role-based route protection (403 Forbidden for non-admins)
- [x] Admin-only user management with pagination and filters
- [x] Role assignment/removal with proper validation
- [x] Admin statistics endpoint
- [x] Protection against self-demotion (admin can't remove own admin role)

---

## Phase 8: Audit Logging System
**Status**: [x] COMPLETED (December 2024)

### Tasks:
- [x] Create `app/core/schemas/audit.py`:
  - [x] `AuditLogResponse` - Schema for single audit log entry
  - [x] `AuditLogListResponse` - Paginated list response
  - [x] `AuditLogFilter` - Filter parameters for queries
  - [x] `AuditStatsResponse` - Statistics response
  - [x] `ActionTypeList`, `EntityTypeList` - Available filter values
- [x] Create `app/core/services/audit_service.py`:
  - [x] `log_action(...)` - Generic action logging
  - [x] `log_login(...)`, `log_logout(...)`, `log_registration(...)` - Auth events
  - [x] `log_password_change(...)` - Password changes
  - [x] `log_user_update(...)`, `log_user_deactivate(...)` - User changes
  - [x] `log_role_assign(...)`, `log_role_remove(...)` - Role changes
  - [x] `log_session_revoke(...)`, `log_all_sessions_revoke(...)` - Session events
  - [x] `log_2fa_enable(...)`, `log_2fa_disable(...)`, `log_2fa_verify(...)` - 2FA events
  - [x] `get_audit_logs(filters, pagination)` - Query with filters
  - [x] `get_audit_log(log_id)` - Get single log
  - [x] `get_stats(from_date, to_date)` - Statistics
  - [x] `get_login_history(user_id, limit)` - Login/logout history
  - [x] `get_user_audit_history(user_id, limit)` - User activity
  - [x] `get_entity_audit_history(entity_type, entity_id, limit)` - Entity history
  - [x] `enrich_logs_with_usernames(logs)` - Add username to logs
  - [x] `cleanup_old_logs(days)` - Retention management
- [x] Implement audit logging calls in:
  - [x] Auth service (login, logout, register, password change, session management)
  - [x] User service (updates tracked via admin endpoints)
  - [x] Role service (assignments tracked via admin endpoints)
  - [x] Session service (revocations)
  - [x] 2FA service (enable/disable/verify via auth service)
- [x] Add audit endpoints to `app/core/routers/admin.py`:
  - [x] `GET /admin/audit-logs` - List with pagination and filters
  - [x] `GET /admin/audit-logs/stats` - Statistics endpoint
  - [x] `GET /admin/audit-logs/login-history` - Login/logout history
  - [x] `GET /admin/audit-logs/action-types` - Available action types
  - [x] `GET /admin/audit-logs/entity-types` - Available entity types
  - [x] `GET /admin/audit-logs/user/{user_id}` - User's activity history
  - [x] `GET /admin/audit-logs/{log_id}` - Get specific log details
- [x] Implement filters:
  - [x] By user_id
  - [x] By action_type (LOGIN, LOGOUT, REGISTER, PASSWORD_CHANGE, etc.)
  - [x] By entity_type (USER, ROLE, SESSION, TWO_FACTOR, etc.)
  - [x] By entity_id
  - [x] By date range (from_date, to_date)
  - [x] By workflow_schema
  - [x] By ip_address

### Deliverables:
- [x] Complete audit trail for all core actions
- [x] Filterable audit log API with pagination
- [x] Changes tracked as JSON (old/new values)
- [x] Statistics endpoint with action type and entity type breakdowns
- [x] Login history endpoint for security monitoring
- [x] Username enrichment for better readability

---

## Phase 9: Middleware & Security Hardening
**Status**: [x] **COMPLETED**

### Tasks:
- [x] Create `app/middleware/request_id.py`:
  - [x] Generate/propagate X-Request-ID header
  - [x] Context variable for logging integration
- [x] Create `app/middleware/security_headers.py`:
  - [x] X-Content-Type-Options: nosniff
  - [x] X-Frame-Options: DENY
  - [x] X-XSS-Protection: 1; mode=block
  - [x] Referrer-Policy: strict-origin-when-cross-origin
  - [x] Permissions-Policy (restrict browser features)
  - [x] Strict-Transport-Security (enabled in production)
  - [x] Cache-Control for API endpoints
- [x] Create `app/middleware/rate_limit.py`:
  - [x] 60 requests/minute per IP (general)
  - [x] 10 requests/minute per IP (auth endpoints)
  - [x] Token bucket algorithm implementation
  - [x] X-RateLimit-* headers in responses
  - [x] Return 429 Too Many Requests with Retry-After
- [x] Create `app/core/models/password_reset.py`:
  - [x] PasswordResetToken model with secure hashing
  - [x] Token expiry (30 minutes)
  - [x] IP/User-Agent tracking
- [x] Create `app/core/services/password_reset_service.py`:
  - [x] Token generation with SHA-256 hashing
  - [x] Token validation and consumption
  - [x] Automatic cleanup of old tokens
- [x] Implement password reset endpoints:
  - [x] `POST /auth/forgot-password` - Request reset token
  - [x] `POST /auth/reset-password` - Reset with token
- [x] Implement account lockout:
  - [x] Track failed login attempts in User model
  - [x] Lock account after 5 failed attempts
  - [x] Auto-unlock after 15 minutes
  - [x] AccountLockedException with retry time
  - [x] Audit logging for lockouts and failed attempts
- [x] Register all middleware in `main.py`
- [x] Configure CORS properly with specific headers

### Deliverables:
- Request ID tracking via X-Request-ID header
- Security headers on all responses
- Rate limiting active with headers
- Password reset flow (forgot password + reset)
- Account lockout protection

---

## Phase 10: Testing & Documentation
**Status**: [x] **COMPLETED**

### Tasks:
- [x] Create `requirements-dev.txt` with test dependencies:
  - [x] pytest, pytest-asyncio, pytest-cov
  - [x] httpx for async client testing
  - [x] factory-boy, faker for test data
  - [x] aiosqlite for in-memory testing
  - [x] ruff, black, mypy for code quality
- [x] Create `tests/conftest.py`:
  - [x] SQLite in-memory test database
  - [x] Test database fixtures with auto-cleanup
  - [x] Test client fixture with ASGI transport
  - [x] Authenticated user fixtures (standard + admin)
  - [x] Auth header fixtures
  - [x] Helper assertion functions
- [x] Write unit tests in `tests/core/`:
  - [x] `test_auth.py` - Registration, login, logout, refresh, password reset, lockout
  - [x] `test_users.py` - User CRUD, role management, admin stats
  - [x] `test_sessions.py` - Session listing, revocation
  - [x] `test_two_factor.py` - 2FA setup/verify/login/backup codes
  - [x] `test_audit.py` - Audit log access, stats, history
- [x] Write integration tests (`tests/test_integration.py`):
  - [x] Full registration to logout flow
  - [x] Complete 2FA setup and login flow
  - [x] Password reset flow
  - [x] Role-based access control
  - [x] Session management
  - [x] Security middleware verification
- [x] Create `pytest.ini` with test configuration
- [x] Create `scripts/create_admin.py`:
  - [x] Interactive mode with prompts
  - [x] CLI arguments for automation
  - [x] Password validation
  - [x] Role assignment
- [x] Write comprehensive `README.md`:
  - [x] Complete feature documentation
  - [x] API endpoint reference
  - [x] Environment variable documentation
  - [x] Development and testing guide
  - [x] Security features documentation
  - [x] Production deployment checklist

### Deliverables:
- Complete test suite with unit and integration tests
- Interactive API docs at `/docs`
- Admin creation script (`scripts/create_admin.py`)
- Comprehensive README with full documentation

---

## Summary Progress Tracker

| Phase | Description | Status | Completion |
|-------|-------------|--------|------------|
| 1 | Project Setup & Foundation | **COMPLETED** | 100% |
| 2 | Database Models (Core App) | **COMPLETED** | 100% |
| 3 | Shared Utilities & Responses | **COMPLETED** | 100% |
| 4 | Authentication System | **COMPLETED** | 100% |
| 5 | Session Management | **COMPLETED** | 100% |
| 6 | Two-Factor Authentication | **COMPLETED** | 100% |
| 7 | Role-Based Access Control | **COMPLETED** | 100% |
| 8 | Audit Logging System | **COMPLETED** | 100% |
| 9 | Middleware & Security | **COMPLETED** | 100% |
| 10 | Testing & Documentation | **COMPLETED** | 100% |

**Overall Progress**: 10/10 Phases Complete - CORE APP COMPLETE!

---

## Dependencies

### requirements.txt
```
# Core Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy[asyncio]>=2.0.25
asyncpg>=0.29.0
alembic>=1.13.0

# Authentication & Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pyotp>=2.9.0
qrcode[pil]>=7.4.2

# Validation
email-validator>=2.1.0

# HTTP
python-multipart>=0.0.6
aiofiles>=23.2.1

# Rate Limiting
slowapi>=0.1.9
```

### requirements-dev.txt
```
# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
httpx>=0.26.0

# Code Quality
black>=23.12.0
isort>=5.13.0
flake8>=7.0.0
mypy>=1.8.0
```

---

## Configuration (.env.example)

```env
# ═══════════════════════════════════════════════════════════
# LANDFILL MANAGEMENT SYSTEM - ENVIRONMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Application
APP_NAME="Landfill Management System"
APP_VERSION="1.0.0"
DEBUG=true
API_PREFIX="/api/v1"

# Database
DATABASE_URL=postgresql+asyncpg://landfill_user:landfill_pass@localhost:5432/landfill_db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
BCRYPT_ROUNDS=12
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_UNAUTHENTICATED=20
ACCOUNT_LOCKOUT_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=15

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# File Storage (for future workflow)
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
```

---

## Docker Compose (docker-compose.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: landfill_postgres
    environment:
      POSTGRES_USER: landfill_user
      POSTGRES_PASSWORD: landfill_pass
      POSTGRES_DB: landfill_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./Landfill_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U landfill_user -d landfill_db"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

---

## Adding a New Workflow (Future Reference)

To add a new workflow (e.g., `equipment_tracking`):

1. **Copy template**:
   ```bash
   cp -r app/workflows/_template app/workflows/equipment_tracking
   ```

2. **Create database schema**:
   ```sql
   CREATE SCHEMA IF NOT EXISTS equipment_tracking;
   ```

3. **Implement models, schemas, routers, services** in the new folder

4. **Create Alembic migration**:
   ```bash
   alembic revision --autogenerate -m "add equipment_tracking schema"
   ```

5. **Register workflow** in `app/workflows/__init__.py`:
   ```python
   from app.workflows.equipment_tracking.routers import router as equipment_router

   def register_workflows(app):
       # ... existing workflows ...
       app.include_router(equipment_router, prefix="/equipment", tags=["Equipment Tracking"])
   ```

6. **Add to workflows table**:
   ```sql
   INSERT INTO core_app.workflows (workflow_name, workflow_code, schema_name)
   VALUES ('Equipment Tracking', 'equipment_tracking', 'equipment_tracking');
   ```

---

## Next Milestone: Landfill Workflow

After completing the Core App (Phases 1-10), the next milestone will be:

### Workflow 1: Landfill Document Management
- PDF upload and storage
- LLM integration (GPT-4 Vision / Claude) for extraction
- Weigh slips CRUD with site assignment
- Hazardous slips with base64 image storage
- Construction sites management
- User-site access control
- Excel export functionality

---

*Last Updated: December 2024*
