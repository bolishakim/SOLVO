# Frontend Development Plan
## Landfill Management System - Next.js Implementation

---

## Overview

This document outlines the step-by-step implementation plan for the Next.js frontend. Each phase builds upon the previous one, ensuring a logical progression from foundation to complete application.

**Total Phases**: 8
**Tech Stack**: Next.js 14, TypeScript, shadcn/ui, Tailwind CSS, React Query, React Hook Form

### ⚠️ IMPORTANT: German Localization Requirement
**All user-facing text must be in German.** This includes:
- Navigation labels, page titles, descriptions
- Form labels, placeholders, validation messages
- Toast notifications and alerts
- Button text and action labels
- All visible UI text

Use the centralized translations file: `src/lib/translations.ts`
```typescript
import { t } from '@/lib/translations';
// Example: t.pages.profile.title → "Profileinstellungen"
```

---

## Phase 1: Project Setup & Foundation ✅ COMPLETED

### 1.1 Initialize Next.js Project ✅
```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
cd frontend
```

### 1.2 Install Core Dependencies ✅
```bash
# UI Components
npx shadcn@latest init
npx shadcn@latest add button card input label form select checkbox dialog alert dropdown-menu avatar badge separator tabs table skeleton popover command calendar sonner

# Additional packages
npm install @tanstack/react-query axios react-hook-form @hookform/resolvers zod
npm install lucide-react date-fns
npm install js-cookie @types/js-cookie
```

### 1.3 Project Structure ✅
```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── forgot-password/
│   │   │   ├── reset-password/
│   │   │   ├── 2fa-verify/
│   │   │   ├── verify-email/
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/
│   │   │   ├── dashboard/
│   │   │   ├── profile/
│   │   │   ├── admin/
│   │   │   ├── landfill/
│   │   │   └── layout.tsx
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/              # shadcn components
│   │   ├── layout/          # Layout components
│   │   ├── forms/           # Form components
│   │   └── shared/          # Shared components
│   ├── lib/
│   │   ├── api.ts           # Axios instance
│   │   ├── utils.ts         # Helper functions
│   │   └── validations.ts   # Zod schemas
│   ├── services/
│   │   └── auth.ts          # Auth API hooks
│   ├── types/
│   │   ├── api.ts           # API types
│   │   ├── user.ts
│   │   ├── landfill.ts
│   │   ├── audit.ts
│   │   └── index.ts
│   └── providers/
│       ├── query-provider.tsx
│       └── auth-provider.tsx
├── public/
├── .env.local
└── package.json
```

### 1.4 Configure Environment ✅
```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Landfill Management System
```

### 1.5 Setup API Client ✅
**File**: `src/lib/api.ts`
- Axios instance with base URL from environment
- Request interceptor for adding auth token
- Response interceptor for token refresh on 401
- Helper functions: setTokens, clearTokens, getAccessToken, isAuthenticated

### 1.6 Setup Providers ✅
**File**: `src/providers/query-provider.tsx`
- React Query client with default options
- 1 minute stale time, 1 retry, no refetch on window focus

### 1.7 Define Base Types ✅
**Files created**:
- `src/types/api.ts` - ApiResponse, PaginatedResponse, ApiError
- `src/types/user.ts` - User, Tokens, LoginCredentials, RegisterData, TwoFactorSetup, Role, Session, etc.
- `src/types/landfill.ts` - WeighSlip, HazardousSlip, ConstructionSite, Company, Location, MaterialType, Document
- `src/types/audit.ts` - AuditLog, LoginHistoryEntry, AuditFilters
- `src/types/index.ts` - Re-exports all types

### Deliverables Phase 1:
- [x] Next.js project initialized
- [x] All dependencies installed
- [x] Folder structure created
- [x] API client configured with token refresh
- [x] Providers set up (React Query)
- [x] Base types defined
- [x] Root layout with providers
- [x] Build verification passed

---

## Phase 2: Authentication Pages ✅ COMPLETED

### 2.1 Auth Layout ✅
**File**: `src/app/(auth)/layout.tsx`
- Split-screen layout with branding on left
- Responsive design (mobile shows header instead)
- Feature highlights list
- Copyright footer

### 2.2 Auth Service Hooks ✅
**File**: `src/services/auth.ts`
- `authApi` - All API functions (login, register, logout, etc.)
- `useLogin` - Login mutation with 2FA handling
- `useRegister` - Registration mutation
- `useLogout` - Logout with token cleanup
- `useForgotPassword` - Password reset request
- `useResetPassword` - Password reset with token
- `useVerifyEmail` - Email verification
- `useResendVerification` - Resend verification email
- `useVerify2FA` - 2FA code verification
- `useVerifyBackupCode` - Backup code verification
- `useSetup2FA`, `useEnable2FA`, `useDisable2FA` - 2FA management
- `useChangePassword` - Password change
- `useCurrentUser` - Get current user query

### 2.3 Auth Provider ✅
**File**: `src/providers/auth-provider.tsx`
- Auth context with user state
- Route protection logic
- Role-based access control (hasRole, hasAnyRole)
- Automatic redirect handling

### 2.4 Form Validations ✅
**File**: `src/lib/validations.ts`
- `loginSchema` - Username/email + password
- `registerSchema` - Full registration with password confirmation
- `forgotPasswordSchema` - Email validation
- `resetPasswordSchema` - Token + new password + confirmation
- `changePasswordSchema` - Current + new password + confirmation
- `twoFactorCodeSchema` - 6-digit code validation
- `backupCodeSchema` - Backup code format validation
- All landfill-related schemas

### 2.5 Login Page ✅
**File**: `src/app/(auth)/login/page.tsx`
- Username/email input
- Password input with show/hide toggle
- Forgot password link
- Register link
- Form validation with Zod
- Loading state with spinner
- Error handling via toast

### 2.6 Register Page ✅
**File**: `src/app/(auth)/register/page.tsx`
- First name, Last name
- Username, Email, Phone (optional)
- Password with strength indicator (4 requirements)
- Confirm password
- Real-time validation feedback
- Success redirect to login

### 2.7 Forgot Password Page ✅
**File**: `src/app/(auth)/forgot-password/page.tsx`
- Email input
- Success confirmation view with email display
- "Try different email" option
- Back to login link

### 2.8 Reset Password Page ✅
**File**: `src/app/(auth)/reset-password/page.tsx`
- Token from URL query parameter
- Invalid/missing token handling
- New password with strength indicator
- Confirm password
- Suspense boundary for useSearchParams

### 2.9 Email Verification Page ✅
**File**: `src/app/(auth)/verify-email/page.tsx`
- Auto-verification on page load with token
- Loading state while verifying
- Success message with login redirect
- Error handling for invalid/expired tokens
- Resend verification email form
- Suspense boundary for useSearchParams

### 2.10 Two-Factor Auth Page ✅
**File**: `src/app/(auth)/2fa-verify/page.tsx`
- 6-digit code input with auto-focus
- Paste support for codes
- Tabs: Authenticator / Backup Code
- Backup code input with format hint
- Session storage for temp token
- Back to login link

### Deliverables Phase 2:
- [x] Auth layout with branding
- [x] Login page with form
- [x] Register page with password strength
- [x] Forgot password page
- [x] Reset password page
- [x] Email verification page
- [x] 2FA verification page (code + backup)
- [x] Auth service hooks
- [x] Auth provider with route protection
- [x] Form validation schemas
- [x] Build verification passed

---

## Phase 3: Dashboard Layout & Navigation ✅ COMPLETED

### 3.1 Dashboard Layout ✅
**File**: `src/app/(dashboard)/layout.tsx`

**Features Implemented**:
- Sidebar navigation with collapsible state
- Top header with breadcrumbs and user menu
- Main content area with proper spacing
- Fully responsive design
- Protected route wrapper with auth check
- Loading state while checking authentication

### 3.2 Sidebar Component ✅
**File**: `src/components/layout/sidebar.tsx`

**Features Implemented**:
- Logo/Brand display
- Navigation links with Lucide icons
- Collapsible sidebar with tooltips when collapsed
- Active state indicator with background highlight
- Collapse toggle button
- User-role based menu items (adminOnly flag)
- Scroll area for long menu lists

**Menu Structure**:
```
Übersicht (Dashboard)
Profil (Profile)
├── Einstellungen (Settings)
├── Sicherheit (Security)
├── Sitzungen (Sessions)
└── Anmeldeverlauf (Login History)
Administration (Admin - admin only)
├── Benutzer (Users)
├── Rollen (Roles)
├── Prüfprotokolle (Audit Logs)
├── Anmeldeverlauf (Login History)
├── Sicherheit (Security Dashboard)
└── Statistiken (Statistics)
Deponie (Landfill)
├── Dokumente (Documents)
├── Wiegescheine (Weigh Slips)
├── Gefahrstoffscheine (Hazardous Slips)
├── Baustellen (Sites)
├── Unternehmen (Companies)
├── Standorte (Locations)
├── Materialien (Materials)
└── Export
```

### 3.3 Header Component ✅
**File**: `src/components/layout/header.tsx`

**Features Implemented**:
- Auto-generated breadcrumbs from URL path
- User dropdown menu integration
- Mobile sidebar trigger button

### 3.4 User Menu ✅
**File**: `src/components/layout/user-menu.tsx`

**Features Implemented**:
- User avatar with initials fallback
- User name and email display
- Profile link
- Security link
- Settings link
- Logout button with loading state

### 3.5 Page Header Component ✅
**File**: `src/components/layout/page-header.tsx`

**Features Implemented**:
- Title display
- Optional description
- Action buttons slot

### 3.6 Mobile Sidebar ✅
**File**: `src/components/layout/mobile-sidebar.tsx`

**Features Implemented**:
- Sheet-based mobile navigation
- Same navigation structure as desktop
- Auto-close on link click
- Hamburger menu trigger

### 3.7 Breadcrumbs Component ✅
**File**: `src/components/layout/breadcrumbs.tsx`

**Features Implemented**:
- Auto-generates from pathname
- German labels from translations
- Home icon for dashboard
- Clickable intermediate segments
- Current page non-clickable

### 3.8 Auth Protection ✅
Implemented in dashboard layout with:
- Authentication check on mount
- Redirect to login if not authenticated
- Loading state while checking
- User data fetching via useCurrentUser hook

### 3.9 German Localization ✅
**File**: `src/lib/translations.ts`

**Features Implemented**:
- Centralized German translations file
- All navigation labels in German
- All page titles and descriptions in German
- Toast messages in German
- Validation messages in German
- Breadcrumb labels in German

### Deliverables Phase 3:
- [x] Dashboard layout with sidebar
- [x] Sidebar navigation component
- [x] Header component
- [x] User dropdown menu
- [x] Breadcrumbs component
- [x] Page header component
- [x] Protected route wrapper
- [x] Role-based menu rendering
- [x] Responsive sidebar (mobile)
- [x] German translations for all UI text
- [x] Coming soon placeholder pages for all routes

---

## Phase 4: Dashboard & Profile Pages ✅ COMPLETED

### 4.1 Main Dashboard ✅
**File**: `src/app/(dashboard)/dashboard/page.tsx`

**Features Implemented**:
- Welcome message with user's first name
- Stats cards (Documents, Weigh Slips, Active Sites, Hazardous Materials)
- Trend indicators with percentages
- Recent activity feed with timestamps
- Quick actions grid (Upload, New Weigh Slip, Manage Sites, Review Hazardous)

**Components Created**:
- `QuickActionButton` - Action link with icon

### 4.2 Profile Page ✅
**File**: `src/app/(dashboard)/profile/page.tsx`

**Features Implemented**:
- User info display with account status sidebar
- Edit form (first name, last name, phone)
- Editable/readonly mode toggle
- Account status badges (active, verified, 2FA)
- Member since and last login dates
- German date formatting with date-fns de locale
- Loading skeleton state
- Success/error toast feedback

### 4.3 Security Settings ✅
**File**: `src/app/(dashboard)/profile/security/page.tsx`

**Features Implemented**:
- Change password form with show/hide toggles
- Current password validation
- New password with confirmation
- 2FA setup flow with QR code placeholder
- 2FA enable/disable with code verification
- Backup codes display with copy functionality
- Download backup codes feature
- Regenerate backup codes
- AlertDialog confirmations for destructive actions
- Status badges for 2FA state

**Components Created**:
- Inline ChangePasswordForm
- Inline TwoFactorSetup section
- Inline BackupCodesDisplay

### 4.4 Sessions Management ✅
**File**: `src/app/(dashboard)/profile/sessions/page.tsx`

**Features Implemented**:
- Active sessions cards display
- Current session highlighting with badge
- Device/browser parsing from user agent
- Device icons (Monitor, Smartphone, Tablet)
- IP address and last activity display
- German date formatting
- Revoke single session with confirmation
- Revoke all other sessions with confirmation
- Loading skeleton state
- Empty state handling

### 4.5 Login History (User) ✅
**File**: `src/app/(dashboard)/profile/login-history/page.tsx`

**Features Implemented**:
- Table of user's login attempts
- Columns: Date/Time, Status, IP Address, Device/Browser, Details
- Status badges: Success (green), Failed (red), Logout (gray)
- Filter by status (All, Success, Failed)
- Suspicious activity warning (>3 failed attempts)
- Device/browser parsing with icons
- German date formatting
- Loading skeleton state
- Empty state handling
- Pagination (last 50 logins)

**Components Created**:
- `StatusBadge` - Login status indicator
- `LoginHistoryRow` - Table row component
- `parseUserAgent` - Device/browser parser

### 4.6 Profile Service Hooks ✅
**File**: `src/services/profile.ts`

**Hooks Implemented**:
```typescript
// Profile
export function useProfile() { ... }
export function useUpdateProfile() { ... }

// Sessions
export function useSessions() { ... }
export function useRevokeSession() { ... }
export function useRevokeAllSessions() { ... }

// Login History
export function useLoginHistory(filters?) { ... }

// 2FA
export function use2FAStatus() { ... }
export function useSetup2FA() { ... }
export function useEnable2FA() { ... }
export function useDisable2FA() { ... }
export function useRegenerateBackupCodes() { ... }
```

### Deliverables Phase 4:
- [x] Dashboard page with stats
- [x] Stats cards with trend indicators
- [x] Activity feed component
- [x] Quick actions component
- [x] Profile settings page
- [x] Security settings page
- [x] Password change form
- [x] 2FA setup/disable functionality
- [x] Backup codes display and download
- [x] Sessions management page
- [x] Login history page (user)
- [x] Login history table with status badges
- [x] Device/browser parsing utility
- [x] Profile service hooks (profile, sessions, 2FA)
- [x] German translations for all Phase 4 pages

---

## Phase 5: Admin Pages ✅ COMPLETED

### 5.1 User Management ✅
**File**: `src/app/(dashboard)/admin/users/page.tsx`

**Features Implemented**:
- Data table with all users
- Columns: Username/Email, Full Name, Roles (badges), Status, 2FA, Verified, Last Login
- Filters: Status (active/inactive/locked), 2FA, Verified, Role
- Pagination with page controls
- Row actions: View, Edit, Unlock (if locked), Activate/Deactivate

**Components Created**:
- `UserRow` - Table row with status badges
- `StatusBadge` - Active/Inactive/Locked status
- Filter selects with clear functionality

### 5.2 User Details ✅
**File**: `src/app/(dashboard)/admin/users/[id]/page.tsx`

**Features Implemented**:
- **User Information Section**: Avatar with initials, username, email, status badges
- **Account Status Sidebar**:
  - Active status with badge
  - 2FA status with badge
  - Email verification status
  - Member since date
  - Last login date
- **Tabs Navigation**:
  - Info tab: Personal information display
  - Login History tab: User's recent logins
  - Activity tab: Audit log entries for this user
- **Role Management**: Assign/remove roles with mutation hooks
- **Security Actions** (via AlertDialog confirmations):
  - Force logout all sessions
  - Reset 2FA
  - Send password reset email
  - Activate/Deactivate account

### 5.3 Role Management ✅
**File**: `src/app/(dashboard)/admin/roles/page.tsx`

**Features Implemented**:
- Roles table with columns: Name, Code (monospace badge), Description, User Count
- Loading skeleton state
- Empty state handling
- User count with icon

### 5.4 Audit Logs ✅
**File**: `src/app/(dashboard)/admin/audit-logs/page.tsx`

**Features Implemented**:
- Logs data table with expandable details
- Advanced filters: Action type, Entity type, Date range
- Collapsible row details showing description and JSON changes
- Action/Entity badges with German translations
- Pagination with page controls
- Clear filters button

**Components Created**:
- `ActionBadge` - Color-coded action type badge
- `EntityBadge` - Entity type badge
- `AuditLogRow` - Expandable table row

### 5.5 Statistics ✅
**File**: `src/app/(dashboard)/admin/stats/page.tsx`

**Features Implemented**:
- **User Stats Cards**: Total users, Active users, Verified users, 2FA adoption rate
- **Activity Stats Cards**: Total logins, Logins today, Failed logins today, Active sessions
- **Audit Stats Cards**: Total logs, Logs last 24h
- **Activity Breakdown**: Progress bar charts for logs by action and by entity type
- Loading skeleton state

**Components Created**:
- `StatCard` - Metric card with icon
- `ActivityBreakdown` - Progress bar chart with percentages

### 5.6 Admin Login History ✅
**File**: `src/app/(dashboard)/admin/login-history/page.tsx`

**Features Implemented**:
- System-wide login history table
- Columns: Date/Time, User, Status, IP Address, Device/Browser, Details
- Filters: Status (All/Success/Failed), Date range
- Export button (UI ready)
- Failed login row highlighting (red background)
- Device/browser parsing with icons

**Components Created**:
- `StatusBadge` - Login/Logout/Failed badges
- `LoginHistoryRow` - Table row with device parsing
- `parseUserAgent` - Device/browser parser utility

### 5.7 Security Dashboard ✅
**File**: `src/app/(dashboard)/admin/security/page.tsx`

**Features Implemented**:
- **Security Overview Cards**:
  - Failed logins (last 24h)
  - Locked accounts count
  - 2FA adoption rate percentage
  - Suspicious activity count
- **Locked Accounts Section**:
  - Table of currently locked accounts
  - Columns: User, Locked At, Unlock Time, Failed Attempts, Action
  - Unlock button with mutation hook
- **Recent Failed Logins Section**:
  - Failed logins from last 24h
  - Repeat offender highlighting (>3 failures, yellow background)
  - Attempt count column
- **Security Recommendations**:
  - Users without 2FA list
  - Inactive accounts (>30 days) list

**Components Created**:
- `StatCard` - Security metric card
- `LockedAccountsTable` - With unlock functionality
- `FailedLoginsTable` - With repeat offender highlighting
- Recommendation cards with user lists

### 5.8 Admin Service ✅
**File**: `src/services/admin.ts`

**Hooks Implemented**:
```typescript
// Users
export function useUsers(filters?: UserFilters) { ... }
export function useUser(userId: string) { ... }
export function useUpdateUser() { ... }
export function useUnlockUser() { ... }
export function useDeactivateUser() { ... }
export function useActivateUser() { ... }

// Roles
export function useRoles() { ... }
export function useAssignRole() { ... }
export function useRemoveRole() { ... }

// Audit Logs
export function useAuditLogs(filters?: AuditLogFilters) { ... }
export function useAuditStats() { ... }

// Login History
export function useAdminLoginHistory(filters?) { ... }

// Security
export function useSecurityStats() { ... }
export function useLockedAccounts() { ... }
export function useFailedLogins(hours?: number) { ... }
export function useUsersWithout2FA() { ... }
export function useInactiveUsers() { ... }

// Security Actions
export function useForceLogout() { ... }
export function useReset2FA() { ... }
export function useSendPasswordReset() { ... }
```

### Deliverables Phase 5:
- [x] Users list page with table
- [x] User details page with tabs (info, login history, activity)
- [x] Role management page
- [x] Audit logs page with filters
- [x] Admin login history page
- [x] Security dashboard page
- [x] Statistics page
- [x] Status badge components (Locked, Verified, 2FA, Active)
- [x] Filter components
- [x] Locked accounts table with unlock
- [x] Unlock account functionality
- [x] Admin API hooks
- [x] German translations for all admin pages

---

## Phase 6: Landfill - Documents & Slips

### 6.1 Documents List
**File**: `src/app/(dashboard)/landfill/documents/page.tsx`

**Features**:
- Documents table
- Status badges
- Filter by status
- Delete action
- Upload button

### 6.2 Document Upload
**File**: `src/app/(dashboard)/landfill/documents/upload/page.tsx`

**Features**:
- Drag & drop zone
- File validation
- Upload progress
- Processing status
- Success feedback

**Components**:
- `FileDropzone`
- `UploadProgress`
- `ProcessingStatus`

### 6.3 Weigh Slips List
**File**: `src/app/(dashboard)/landfill/weigh-slips/page.tsx`

**Features**:
- Full data table
- Advanced filters
- Bulk actions
- Export button
- Manual entry button

### 6.4 Weigh Slip Details
**File**: `src/app/(dashboard)/landfill/weigh-slips/[id]/page.tsx`

**Features**:
- Full information display
- Edit mode
- Assign to site
- Source document link
- Delete action

### 6.5 Manual Weigh Slip Entry
**File**: `src/app/(dashboard)/landfill/weigh-slips/new/page.tsx`

**Features**:
- Full form
- Dropdown selectors
- Date picker
- Validation

### 6.6 Hazardous Slips List
**File**: `src/app/(dashboard)/landfill/hazardous-slips/page.tsx`

Similar to weigh slips with image preview.

### 6.7 Hazardous Slip Details
**File**: `src/app/(dashboard)/landfill/hazardous-slips/[id]/page.tsx`

**Features**:
- Full information
- Image display
- Image zoom/lightbox
- Print button

**Components**:
- `ImageLightbox`

### 6.8 Landfill Hooks
```typescript
// src/hooks/queries/use-landfill.ts
export function useWeighSlips(filters: SlipFilters) { ... }
export function useWeighSlip(id: string) { ... }
export function useCreateWeighSlip() { ... }
export function useUpdateWeighSlip() { ... }
export function useAssignSlip() { ... }
export function useUploadDocument() { ... }
```

### Deliverables Phase 6:
- [ ] Documents list page
- [ ] Document upload page
- [ ] File dropzone component
- [ ] Upload progress component
- [ ] Weigh slips list page
- [ ] Weigh slip details page
- [ ] Manual entry form
- [ ] Hazardous slips list page
- [ ] Hazardous slip details with image
- [ ] Image lightbox component
- [ ] Landfill API hooks

---

## Phase 7: Landfill - Sites & Master Data

### 7.1 Construction Sites List
**File**: `src/app/(dashboard)/landfill/sites/page.tsx`

**Features**:
- Sites table
- Search, filter
- Add site button

### 7.2 Site Details
**File**: `src/app/(dashboard)/landfill/sites/[id]/page.tsx`

**Features**:
- Site information
- Edit form
- Assigned users management
- Assigned weigh slips table
- Statistics

### 7.3 Create Site
**File**: `src/app/(dashboard)/landfill/sites/new/page.tsx`

**Features**:
- Site creation form
- User assignment

### 7.4 Companies Management
**File**: `src/app/(dashboard)/landfill/companies/page.tsx`

**Features**:
- CRUD table
- Add/Edit modal
- Delete confirmation

### 7.5 Locations Management
**File**: `src/app/(dashboard)/landfill/locations/page.tsx`

**Features**:
- CRUD table
- Company filter
- Add/Edit modal

### 7.6 Material Types Management
**File**: `src/app/(dashboard)/landfill/materials/page.tsx`

**Features**:
- CRUD table
- Hazardous indicator
- Add/Edit modal

### 7.7 CRUD Modal Component
```typescript
// src/components/shared/crud-modal.tsx
interface CrudModalProps<T> {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: T) => void;
  initialData?: T;
  title: string;
  children: React.ReactNode;
}
```

### Deliverables Phase 7:
- [ ] Sites list page
- [ ] Site details page
- [ ] Create site page
- [ ] Companies CRUD page
- [ ] Locations CRUD page
- [ ] Materials CRUD page
- [ ] CRUD modal component
- [ ] Master data API hooks

---

## Phase 8: Data Export & Polish

### 8.1 Export Page
**File**: `src/app/(dashboard)/landfill/export/page.tsx`

**Features**:
- Format selection (Excel/PDF)
- Date range picker
- Multi-select filters
- Preview count
- Generate button
- Download link
- Export history

### 8.2 Error Handling ✅
**Files Created**:
- `src/app/not-found.tsx` - 404 Not Found page
- `src/app/error.tsx` - Global error boundary
- `src/app/(dashboard)/error.tsx` - Dashboard error boundary
- `src/app/(auth)/error.tsx` - Auth error boundary

**Features Implemented**:
- 404 page with navigation buttons
- Error boundaries at global, dashboard, and auth levels
- Error digest display for debugging
- Retry functionality
- German translations for all error messages

### 8.3 Loading States ✅
- Page-level skeletons (implemented across all pages)
- Component-level skeletons
- Button loading states with spinners

### 8.4 Notifications ✅
- Toast notifications via Sonner (already set up)
- Success/error messages in German
- AlertDialog confirmations for destructive actions

### 8.5 Accessibility
- Keyboard navigation
- Focus management
- ARIA labels
- Color contrast check

### 8.6 Performance
- Image optimization
- Code splitting verification
- Bundle size check

### 8.7 Testing
- Unit tests for utilities
- Component tests
- Integration tests for forms

### Deliverables Phase 8:
- [ ] Export page (landfill-specific, deferred)
- [x] Error boundary (global + dashboard + auth)
- [x] 404 page
- [x] Toast notification system (Sonner)
- [x] Confirmation dialog component (AlertDialog)
- [x] Loading skeletons (all pages)
- [ ] Accessibility audit
- [ ] Performance audit
- [ ] Test coverage

---

## Development Checklist

### Phase 1: Foundation ✅ COMPLETED
- [x] Project setup
- [x] Dependencies installed
- [x] API client configured
- [x] Providers set up
- [x] Types defined

### Phase 2: Authentication ✅ COMPLETED
- [x] Login page
- [x] Register page
- [x] Forgot password
- [x] Reset password
- [x] 2FA page
- [x] Email verification page
- [x] Auth hooks
- [x] Auth provider

### Phase 3: Layout ✅ COMPLETED
- [x] Dashboard layout
- [x] Sidebar (collapsible, tooltips)
- [x] Mobile sidebar (sheet-based)
- [x] Header with breadcrumbs
- [x] User menu
- [x] Protected routes
- [x] German translations
- [x] Placeholder pages for all routes

### Phase 4: Dashboard & Profile ✅ COMPLETED
- [x] Dashboard page with stats
- [x] Profile page
- [x] Security settings with 2FA
- [x] Sessions page
- [x] Login history page (user)
- [x] Profile service hooks

### Phase 5: Admin ✅ COMPLETED
- [x] Users management
- [x] User details with login history
- [x] Roles management
- [x] Audit logs
- [x] Admin login history
- [x] Security dashboard
- [x] Locked accounts management
- [x] Statistics
- [x] Admin service hooks

### Phase 6: Documents & Slips
- [ ] Documents list
- [ ] Upload page
- [ ] Weigh slips list
- [ ] Weigh slip details
- [ ] Manual entry
- [ ] Hazardous slips

### Phase 7: Sites & Master Data
- [ ] Sites management
- [ ] Companies CRUD
- [ ] Locations CRUD
- [ ] Materials CRUD

### Phase 8: Polish ✅ PARTIALLY COMPLETED
- [ ] Export page (landfill-specific)
- [x] Error handling (404, error boundaries)
- [x] Loading states (skeletons implemented)
- [ ] Accessibility audit
- [ ] Testing

---

## Files Created Summary

### Phase 1 Files:
- `frontend/.env.local`
- `frontend/.env.example`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/validations.ts`
- `frontend/src/providers/query-provider.tsx`
- `frontend/src/types/api.ts`
- `frontend/src/types/user.ts`
- `frontend/src/types/landfill.ts`
- `frontend/src/types/audit.ts`
- `frontend/src/types/index.ts`
- `frontend/src/app/layout.tsx` (updated)
- `frontend/src/app/page.tsx` (updated)

### Phase 2 Files:
- `frontend/src/services/auth.ts`
- `frontend/src/providers/auth-provider.tsx`
- `frontend/src/app/(auth)/layout.tsx`
- `frontend/src/app/(auth)/login/page.tsx`
- `frontend/src/app/(auth)/register/page.tsx`
- `frontend/src/app/(auth)/forgot-password/page.tsx`
- `frontend/src/app/(auth)/reset-password/page.tsx`
- `frontend/src/app/(auth)/verify-email/page.tsx`
- `frontend/src/app/(auth)/2fa-verify/page.tsx`

### Phase 3 Files:
- `frontend/src/lib/translations.ts` - German translations
- `frontend/src/components/layout/sidebar.tsx` - Collapsible sidebar
- `frontend/src/components/layout/mobile-sidebar.tsx` - Mobile sheet sidebar
- `frontend/src/components/layout/header.tsx` - Header with breadcrumbs
- `frontend/src/components/layout/user-menu.tsx` - User dropdown menu
- `frontend/src/components/layout/breadcrumbs.tsx` - Auto-generated breadcrumbs
- `frontend/src/components/layout/page-header.tsx` - Page title component
- `frontend/src/components/layout/index.ts` - Layout exports
- `frontend/src/components/shared/coming-soon.tsx` - Placeholder component
- `frontend/src/app/(dashboard)/layout.tsx` - Dashboard layout with auth
- `frontend/src/app/(dashboard)/dashboard/page.tsx` - Main dashboard
- `frontend/src/app/(dashboard)/profile/page.tsx` - Profile placeholder
- `frontend/src/app/(dashboard)/profile/security/page.tsx` - Security placeholder
- `frontend/src/app/(dashboard)/profile/sessions/page.tsx` - Sessions placeholder
- `frontend/src/app/(dashboard)/profile/login-history/page.tsx` - Login history placeholder
- `frontend/src/app/(dashboard)/admin/users/page.tsx` - Users placeholder
- `frontend/src/app/(dashboard)/admin/roles/page.tsx` - Roles placeholder
- `frontend/src/app/(dashboard)/admin/audit-logs/page.tsx` - Audit logs placeholder
- `frontend/src/app/(dashboard)/admin/login-history/page.tsx` - Admin login history placeholder
- `frontend/src/app/(dashboard)/admin/security/page.tsx` - Admin security placeholder
- `frontend/src/app/(dashboard)/admin/stats/page.tsx` - Statistics placeholder
- `frontend/src/app/(dashboard)/landfill/documents/page.tsx` - Documents placeholder
- `frontend/src/app/(dashboard)/landfill/weigh-slips/page.tsx` - Weigh slips placeholder
- `frontend/src/app/(dashboard)/landfill/hazardous-slips/page.tsx` - Hazardous slips placeholder
- `frontend/src/app/(dashboard)/landfill/sites/page.tsx` - Sites placeholder
- `frontend/src/app/(dashboard)/landfill/companies/page.tsx` - Companies placeholder
- `frontend/src/app/(dashboard)/landfill/locations/page.tsx` - Locations placeholder
- `frontend/src/app/(dashboard)/landfill/materials/page.tsx` - Materials placeholder
- `frontend/src/app/(dashboard)/landfill/export/page.tsx` - Export placeholder

### Phase 4 Files:
- `frontend/src/services/profile.ts` - Profile, sessions, 2FA API hooks
- `frontend/src/lib/translations.ts` (updated) - Added profile, security, sessions, loginHistory German translations
- `frontend/src/app/(dashboard)/profile/page.tsx` - Profile settings page (replaced placeholder)
- `frontend/src/app/(dashboard)/profile/security/page.tsx` - Security settings with 2FA (replaced placeholder)
- `frontend/src/app/(dashboard)/profile/sessions/page.tsx` - Sessions management (replaced placeholder)
- `frontend/src/app/(dashboard)/profile/login-history/page.tsx` - Login history table (replaced placeholder)

### Phase 5 Files:
- `frontend/src/services/admin.ts` - Admin service with all API hooks (users, roles, audit, security)
- `frontend/src/lib/translations.ts` (updated) - Added extensive admin German translations
- `frontend/src/components/ui/collapsible.tsx` - Collapsible component from shadcn
- `frontend/src/app/(dashboard)/admin/users/page.tsx` - User management with table, filters, pagination
- `frontend/src/app/(dashboard)/admin/users/[id]/page.tsx` - User details with tabs and security actions
- `frontend/src/app/(dashboard)/admin/roles/page.tsx` - Roles table (replaced placeholder)
- `frontend/src/app/(dashboard)/admin/audit-logs/page.tsx` - Audit logs with expandable details (replaced placeholder)
- `frontend/src/app/(dashboard)/admin/login-history/page.tsx` - System-wide login history (replaced placeholder)
- `frontend/src/app/(dashboard)/admin/security/page.tsx` - Security dashboard with stats (replaced placeholder)
- `frontend/src/app/(dashboard)/admin/stats/page.tsx` - Statistics with breakdowns (replaced placeholder)

### Phase 8 Files (Error Handling):
- `frontend/src/app/not-found.tsx` - 404 Not Found page
- `frontend/src/app/error.tsx` - Global error boundary
- `frontend/src/app/(dashboard)/error.tsx` - Dashboard error boundary
- `frontend/src/app/(auth)/error.tsx` - Auth error boundary
- `frontend/src/lib/translations.ts` (updated) - Added error page German translations

---

## Quick Start Commands

```bash
# Create project
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir

# Navigate and install
cd frontend
npm install @tanstack/react-query axios react-hook-form @hookform/resolvers zod lucide-react date-fns js-cookie @types/js-cookie

# Add shadcn components
npx shadcn@latest init
npx shadcn@latest add button card input label form select checkbox dialog alert dropdown-menu avatar badge separator tabs table skeleton popover command calendar sheet sonner

# Run development
npm run dev
```

---

**End of Frontend Development Plan**
