# Frontend Product Requirements Document (PRD)
## Landfill Management System - Next.js Frontend

---

## 1. Project Overview

**Purpose**: Build a modern, responsive frontend for the Landfill Management System using Next.js and React with a professional UI component library.

**Target Users**: Construction site managers, waste management operators, system administrators

**Tech Stack**:
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI Library**: shadcn/ui + Tailwind CSS
- **State Management**: React Query (TanStack Query) for server state
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios
- **Authentication**: JWT tokens with refresh mechanism
- **Icons**: Lucide React

---

## 2. Design Principles

### 2.1 UI/UX Guidelines
- **Clean & Professional**: Business application aesthetic
- **Responsive**: Mobile-first design, works on all screen sizes
- **Accessible**: WCAG 2.1 AA compliance
- **Consistent**: Unified design language across all pages
- **Fast**: Optimistic updates, skeleton loaders, minimal load times

### 2.2 Color Scheme
```
Primary: Blue (#3B82F6)
Success: Green (#22C55E)
Warning: Yellow (#F59E0B)
Error: Red (#EF4444)
Background: White/Gray (#FFFFFF, #F9FAFB)
Text: Dark Gray (#111827)
```

### 2.3 Typography
- **Font**: Inter (Google Fonts)
- **Headings**: Bold, hierarchical sizing
- **Body**: Regular weight, good line-height for readability

---

## 3. Application Structure

### 3.1 Route Structure
```
/                           → Redirect to /dashboard or /login
/login                      → Login page
/register                   → Registration page
/forgot-password            → Password reset request
/reset-password             → Password reset form
/2fa                        → Two-factor authentication verification

/dashboard                  → Main dashboard (protected)
/profile                    → User profile settings
/profile/security           → Security settings (password, 2FA)
/profile/sessions           → Active sessions management
/profile/login-history      → Personal login history

/verify-email               → Email verification page
/verify-email/resend        → Resend verification email

/admin/users                → User management (admin only)
/admin/users/[id]           → User details
/admin/roles                → Role management
/admin/audit-logs           → Audit log viewer
/admin/login-history        → System-wide login history
/admin/security             → Security dashboard (failed logins, locked accounts)
/admin/stats                → System statistics

/landfill/documents         → PDF document list
/landfill/documents/upload  → PDF upload page
/landfill/weigh-slips       → Weigh slips list
/landfill/weigh-slips/[id]  → Weigh slip details
/landfill/weigh-slips/new   → Manual weigh slip entry
/landfill/hazardous-slips   → Hazardous slips list
/landfill/hazardous-slips/[id] → Hazardous slip details

/landfill/sites             → Construction sites list
/landfill/sites/[id]        → Site details & assigned slips
/landfill/sites/new         → Create new site

/landfill/companies         → Company management
/landfill/locations         → Location management
/landfill/materials         → Material types management

/landfill/export            → Data export page
```

### 3.2 Layout Structure
```
├── (auth)/                 → Auth layout (centered, no sidebar)
│   ├── login/
│   ├── register/
│   ├── forgot-password/
│   ├── reset-password/
│   ├── 2fa/
│   └── verify-email/
│
├── (dashboard)/            → Dashboard layout (sidebar + header)
│   ├── dashboard/
│   ├── profile/
│   ├── admin/
│   └── landfill/
│
└── layout.tsx              → Root layout (providers, fonts)
```

---

## 4. Page Specifications

### 4.1 Authentication Pages

#### Login Page (`/login`)
**Features:**
- Email/Username input field
- Password input with show/hide toggle
- "Remember me" checkbox
- "Forgot password?" link
- "Create account" link
- Form validation (client-side)
- Loading state during submission
- Error message display
- Redirect to dashboard on success
- Handle 2FA requirement redirect

**API Integration:**
```typescript
POST /api/v1/auth/login
Body: { username_or_email: string, password: string }
Response: { tokens, user } or { requires_2fa: true, temp_token: string }
```

#### Register Page (`/register`)
**Features:**
- Multi-step form:
  - Step 1: Username, Email
  - Step 2: Password, Confirm Password (with strength indicator)
  - Step 3: First Name, Last Name, Phone (optional)
- Real-time validation
- Password requirements display
- Terms acceptance checkbox
- Success message with redirect to login

**API Integration:**
```typescript
POST /api/v1/auth/register
Body: { username, email, password, first_name, last_name, phone_number? }
```

#### Two-Factor Authentication (`/2fa`)
**Features:**
- 6-digit code input (auto-focus, auto-submit)
- "Use backup code" option
- Resend code option (if applicable)
- Timer display
- Error handling

**API Integration:**
```typescript
POST /api/v1/auth/login/2fa
Body: { temp_token: string, code: string }

POST /api/v1/auth/login/backup-code
Body: { temp_token: string, backup_code: string }
```

#### Forgot Password (`/forgot-password`)
**Features:**
- Email input
- Success message (same for all cases - security)
- "Back to login" link

**API Integration:**
```typescript
POST /api/v1/auth/forgot-password
Body: { email: string }
```

#### Reset Password (`/reset-password`)
**Features:**
- Token from URL query parameter
- New password input with strength indicator
- Confirm password input
- Success redirect to login

**API Integration:**
```typescript
POST /api/v1/auth/reset-password
Body: { token: string, new_password: string }
```

#### Email Verification (`/verify-email`)
**Features:**
- Token from URL query parameter
- Auto-verification on page load
- Success message with login redirect
- Error handling for invalid/expired tokens
- "Resend verification email" link

**API Integration:**
```typescript
POST /api/v1/auth/verify-email
Body: { token: string }

POST /api/v1/auth/verify-email/resend
Body: { email: string }
```

#### Account Locked Notice
**Features:**
- Display when login fails due to account lockout
- Shows lockout duration remaining
- Contact admin option
- Retry timer countdown

---

### 4.2 Dashboard

#### Main Dashboard (`/dashboard`)
**Features:**
- Welcome message with user name
- Stats cards:
  - For Admin: Total users, Active sessions, 2FA adoption, Logins today
  - For User: Active sessions, Last login, Account age
- Recent activity feed
- Quick action buttons
- System status (admin only)

**Components:**
- `StatsCard` - Displays metric with icon, value, trend
- `ActivityFeed` - List of recent actions
- `QuickActions` - Button grid for common tasks

**API Integration:**
```typescript
GET /api/v1/auth/me
GET /api/v1/admin/stats (admin only)
```

---

### 4.3 Profile Pages

#### Profile Settings (`/profile`)
**Features:**
- Avatar display (initials-based)
- Editable fields: First name, Last name, Phone
- Read-only fields: Username, Email
- Save changes button
- Success/error toast notifications

**API Integration:**
```typescript
GET /api/v1/auth/me
PUT /api/v1/auth/me
Body: { first_name?, last_name?, phone_number? }
```

#### Security Settings (`/profile/security`)
**Features:**
- Change Password section:
  - Current password input
  - New password input with strength indicator
  - Confirm new password
- Two-Factor Authentication section:
  - Current status display
  - Enable/Disable toggle
  - Setup wizard with QR code
  - Backup codes display (one-time)
- Active Sessions section (link to /profile/sessions)

**API Integration:**
```typescript
POST /api/v1/auth/change-password
Body: { current_password, new_password }

POST /api/v1/auth/2fa/setup
POST /api/v1/auth/2fa/verify
Body: { code: string }

POST /api/v1/auth/2fa/disable
Body: { code: string, password: string }

GET /api/v1/auth/2fa/status
```

#### Sessions Management (`/profile/sessions`)
**Features:**
- List of all active sessions
- Current session indicator
- Session details: IP, Browser, Location, Last active
- Revoke individual session button
- "Revoke all other sessions" button
- Confirmation dialogs

**API Integration:**
```typescript
GET /api/v1/auth/sessions
DELETE /api/v1/auth/sessions/{session_id}
POST /api/v1/auth/sessions/revoke-all
Body: { keep_current: true, current_refresh_token: string }
```

#### Login History (`/profile/login-history`)
**Features:**
- Table of login attempts (success and failed)
- Columns: Date/Time, IP Address, Browser/Device, Location, Status
- Status badges: Success (green), Failed (red)
- Filter by status (All, Success, Failed)
- Date range filter
- Suspicious activity highlighting (unknown location, multiple failures)
- Pagination

**Components:**
- `LoginHistoryTable` - Table with login records
- `LoginStatusBadge` - Success/Failed indicator
- `LocationDisplay` - IP-based location (optional)

**API Integration:**
```typescript
GET /api/v1/admin/audit-logs/login-history?user_id={current_user_id}&limit=50
```

---

### 4.4 Admin Pages

#### User Management (`/admin/users`)
**Features:**
- Data table with columns:
  - Username, Email, Full Name, Roles, Status, Locked, 2FA, Verified, Created, Last Login
- Search (username, email)
- Filters:
  - Status (Active/Inactive)
  - Role
  - 2FA enabled
  - Email verified
  - Account locked
- Pagination
- Row actions: View, Edit, Deactivate, Unlock (if locked)
- Bulk actions (optional)
- "Add User" button (optional - or use registration)
- Quick unlock button for locked accounts

**Components:**
- `DataTable` - Sortable, filterable table with pagination
- `UserStatusBadge` - Active/Inactive indicator
- `LockedBadge` - Locked/Unlocked indicator
- `VerifiedBadge` - Email verified indicator
- `RoleBadge` - Role display chip
- `TwoFactorBadge` - 2FA enabled indicator

**API Integration:**
```typescript
GET /api/v1/admin/users?page=1&page_size=20&search=&is_active=&role_code=
```

#### User Details (`/admin/users/[id]`)
**Features:**
- **User Information Section:**
  - Avatar, Username, Email, Full Name
  - Account status badges (Active/Inactive, Verified/Unverified)
  - 2FA status indicator
  - Created date, Last login date
- **Account Status Section:**
  - Account locked status (if locked)
  - Lock reason and unlock time
  - Failed login attempts count
  - Manual unlock button
  - Force password reset option
- **Edit Form:**
  - Admin-editable fields (name, phone, status)
  - Verify/unverify email toggle
  - Activate/Deactivate account
- **Role Management:**
  - Current roles display
  - Add role dropdown
  - Remove role buttons
- **Login History Tab:**
  - Recent logins for this user
  - Success/Failed status
  - IP and device info
- **Activity History Tab:**
  - Audit log entries for this user
  - All actions performed by user
- **Security Actions:**
  - Force logout all sessions
  - Reset 2FA
  - Send password reset email

**Components:**
- `UserHeader` - User info display with avatar
- `AccountStatusCard` - Lock status, verification
- `UserRoleManager` - Role assignment UI
- `UserLoginHistory` - Embedded login table
- `UserAuditHistory` - Embedded audit table
- `SecurityActionsMenu` - Admin actions dropdown

**API Integration:**
```typescript
GET /api/v1/admin/users/{user_id}
PUT /api/v1/admin/users/{user_id}
GET /api/v1/admin/users/{user_id}/roles
POST /api/v1/admin/users/{user_id}/roles
DELETE /api/v1/admin/users/{user_id}/roles/{role_id}
DELETE /api/v1/admin/users/{user_id}
GET /api/v1/admin/audit-logs/user/{user_id}
GET /api/v1/admin/audit-logs/login-history?user_id={user_id}
POST /api/v1/admin/users/{user_id}/unlock
POST /api/v1/admin/users/{user_id}/force-logout
```

#### Role Management (`/admin/roles`)
**Features:**
- List all roles with user counts
- Role details (description)
- Users in each role (expandable)

**API Integration:**
```typescript
GET /api/v1/admin/roles
```

#### Audit Logs (`/admin/audit-logs`)
**Features:**
- Data table with columns:
  - Timestamp, User, Action, Entity, IP Address, Details
- Filters:
  - Date range picker
  - User selector
  - Action type dropdown
  - Entity type dropdown
  - IP address search
- Expandable row for full details (JSON changes)
- Export to CSV (optional)

**API Integration:**
```typescript
GET /api/v1/admin/audit-logs?page=1&page_size=50&user_id=&action_type=&entity_type=&from_date=&to_date=
GET /api/v1/admin/audit-logs/{log_id}
GET /api/v1/admin/audit-logs/action-types
GET /api/v1/admin/audit-logs/entity-types
```

#### Statistics (`/admin/stats`)
**Features:**
- Summary cards: Total users, Active users, 2FA adoption
- Charts:
  - User registrations over time
  - Login activity chart
  - Users by role pie chart
- Failed login attempts (security)

**API Integration:**
```typescript
GET /api/v1/admin/stats
GET /api/v1/admin/audit-logs/stats
```

#### Login History - Admin (`/admin/login-history`)
**Features:**
- System-wide login history table
- Columns: Date/Time, User, IP Address, Browser/Device, Status
- Filter by:
  - User (searchable dropdown)
  - Status (Success/Failed)
  - Date range
  - IP address
- Export to CSV
- Real-time updates (optional)
- Link to user details from each row

**Components:**
- `AdminLoginHistoryTable` - Full login history
- `UserSelector` - Searchable user dropdown
- `ExportButton` - CSV export

**API Integration:**
```typescript
GET /api/v1/admin/audit-logs/login-history?user_id=&limit=50
```

#### Security Dashboard (`/admin/security`)
**Features:**
- **Security Overview Cards:**
  - Failed logins (last 24h)
  - Locked accounts count
  - Suspicious activity alerts
  - 2FA adoption rate
- **Locked Accounts Section:**
  - Table of currently locked accounts
  - Columns: User, Locked At, Unlock Time, Failed Attempts, Actions
  - Unlock account button (manual override)
- **Failed Login Attempts Section:**
  - Recent failed logins (last 24h)
  - Group by user or IP address
  - Highlight repeat offenders (>3 failures)
- **Suspicious Activity Section:**
  - Multiple IPs per user
  - Unusual login times
  - Geolocation anomalies (if available)
- **Security Recommendations:**
  - Users without 2FA
  - Inactive accounts
  - Accounts with weak passwords (optional)

**Components:**
- `SecurityStatsCard` - Security metric display
- `LockedAccountsTable` - Locked accounts list
- `FailedLoginsChart` - Failed logins over time
- `SuspiciousActivityList` - Alerts list
- `UnlockAccountButton` - Admin unlock action

**API Integration:**
```typescript
GET /api/v1/admin/stats
GET /api/v1/admin/audit-logs/stats
GET /api/v1/admin/audit-logs?action_type=LOGIN_FAILED&from_date={24h_ago}
GET /api/v1/admin/users?is_active=false  // For locked accounts
POST /api/v1/admin/users/{user_id}/unlock  // Unlock account (if implemented)
```

---

### 4.5 Landfill Workflow Pages

#### Documents List (`/landfill/documents`)
**Features:**
- Data table:
  - File name, Upload date, Status, Pages, Extracted slips, Actions
- Status badges: Uploaded, Processing, Completed, Failed
- Filter by status, date range
- View extracted data link
- Delete document (with confirmation)
- "Upload New" button

**API Integration:**
```typescript
GET /api/v1/landfill/documents?page=1&status=
GET /api/v1/landfill/documents/{id}
DELETE /api/v1/landfill/documents/{id}
```

#### Document Upload (`/landfill/documents/upload`)
**Features:**
- Drag & drop zone
- File browser button
- Multiple file support
- File type validation (PDF only)
- Size validation (max 50MB)
- Upload progress indicator
- Processing status updates (polling/websocket)
- Success/failure feedback
- Link to view extracted slips

**Components:**
- `FileDropzone` - Drag & drop area
- `UploadProgress` - Progress bar with status
- `ProcessingStatus` - Status indicator

**API Integration:**
```typescript
POST /api/v1/landfill/documents/upload
Content-Type: multipart/form-data
Body: { file: File }
```

#### Weigh Slips List (`/landfill/weigh-slips`)
**Features:**
- Data table:
  - Slip Number, Date, Site, Material, Company, Weight, Status, Actions
- Advanced filters:
  - Date range
  - Construction site
  - Material type
  - Assignment status (Pending/Assigned)
  - Hazardous (Yes/No)
  - Company/Location
- Bulk assign to site
- Export filtered data
- "Manual Entry" button

**API Integration:**
```typescript
GET /api/v1/landfill/weigh-slips?page=1&site_id=&material_id=&from_date=&to_date=&is_hazardous=&status=
```

#### Weigh Slip Details (`/landfill/weigh-slips/[id]`)
**Features:**
- Full slip information display
- Edit mode for corrections
- Assign to site dropdown
- Link to source document
- Link to related hazardous slip (if applicable)
- Audit history for this slip
- Delete button (soft delete)

**API Integration:**
```typescript
GET /api/v1/landfill/weigh-slips/{id}
PUT /api/v1/landfill/weigh-slips/{id}
POST /api/v1/landfill/weigh-slips/{id}/assign
Body: { site_id: number }
DELETE /api/v1/landfill/weigh-slips/{id}
```

#### Manual Weigh Slip Entry (`/landfill/weigh-slips/new`)
**Features:**
- Form with all weigh slip fields
- Construction site selector
- Material type selector
- Company selector
- Location selector
- Date picker
- Weight input with unit
- Hazardous checkbox
- Save and continue / Save and close

**API Integration:**
```typescript
POST /api/v1/landfill/weigh-slips
Body: { slip_number, delivery_date, site_id, material_id, ... }
```

#### Hazardous Slips List (`/landfill/hazardous-slips`)
**Features:**
- Similar to weigh slips list
- Additional columns: Waste code, Disposal method
- Image preview thumbnail
- Link to full image view

**API Integration:**
```typescript
GET /api/v1/landfill/hazardous-slips?page=1&...
```

#### Hazardous Slip Details (`/landfill/hazardous-slips/[id]`)
**Features:**
- Full slip information
- Full-size image display (from base64)
- Image zoom/lightbox
- Link to related weigh slip
- Print button

**API Integration:**
```typescript
GET /api/v1/landfill/hazardous-slips/{id}
GET /api/v1/landfill/hazardous-slips/{id}/image
```

---

### 4.6 Construction Sites

#### Sites List (`/landfill/sites`)
**Features:**
- Data table:
  - Site Name, Code, Address, Status, Assigned Users, Slip Count, Actions
- Search by name/code
- Filter by status
- "Add Site" button

**API Integration:**
```typescript
GET /api/v1/landfill/construction-sites
```

#### Site Details (`/landfill/sites/[id]`)
**Features:**
- Site information
- Edit form
- Assigned users list with add/remove
- Weigh slips assigned to this site (embedded table)
- Statistics: Total weight, Slip count, Hazardous count

**API Integration:**
```typescript
GET /api/v1/landfill/construction-sites/{id}
PUT /api/v1/landfill/construction-sites/{id}
POST /api/v1/landfill/construction-sites/{id}/assign-user
DELETE /api/v1/landfill/construction-sites/{id}/unassign-user
GET /api/v1/landfill/weigh-slips?site_id={id}
```

#### Create Site (`/landfill/sites/new`)
**Features:**
- Form: Name, Code, Address, Description
- Initial user assignment (optional)

**API Integration:**
```typescript
POST /api/v1/landfill/construction-sites
```

---

### 4.7 Master Data Pages

#### Companies (`/landfill/companies`)
**Features:**
- Simple CRUD table
- Add/Edit modal
- Delete with confirmation

**API Integration:**
```typescript
GET /api/v1/landfill/companies
POST /api/v1/landfill/companies
PUT /api/v1/landfill/companies/{id}
DELETE /api/v1/landfill/companies/{id}
```

#### Locations (`/landfill/locations`)
**Features:**
- CRUD table with company relationship
- Company filter

**API Integration:**
```typescript
GET /api/v1/landfill/locations
POST /api/v1/landfill/locations
PUT /api/v1/landfill/locations/{id}
DELETE /api/v1/landfill/locations/{id}
```

#### Material Types (`/landfill/materials`)
**Features:**
- CRUD table
- Hazardous indicator
- Code and name fields

**API Integration:**
```typescript
GET /api/v1/landfill/material-types
POST /api/v1/landfill/material-types
PUT /api/v1/landfill/material-types/{id}
DELETE /api/v1/landfill/material-types/{id}
```

---

### 4.8 Data Export

#### Export Page (`/landfill/export`)
**Features:**
- Format selection: Excel, PDF
- Date range picker
- Construction site multi-select
- Material type filter
- Hazardous filter
- Preview of data to export (count)
- Generate button
- Download link when ready
- Export history list

**API Integration:**
```typescript
POST /api/v1/landfill/export/excel
POST /api/v1/landfill/export/pdf
Body: { from_date, to_date, site_ids[], material_ids[], is_hazardous }

GET /api/v1/landfill/exports/{export_id}/download
```

---

## 5. Shared Components

### 5.1 Layout Components
| Component | Description |
|-----------|-------------|
| `AppShell` | Main layout wrapper with sidebar and header |
| `Sidebar` | Navigation sidebar with collapsible sections |
| `Header` | Top header with user menu and notifications |
| `Breadcrumbs` | Navigation breadcrumbs |
| `PageHeader` | Page title with actions |

### 5.2 Data Display
| Component | Description |
|-----------|-------------|
| `DataTable` | Full-featured table with sorting, filtering, pagination |
| `StatsCard` | Metric display card |
| `Badge` | Status/role indicator |
| `Avatar` | User avatar with initials fallback |
| `EmptyState` | No data placeholder |
| `Skeleton` | Loading placeholder |

### 5.3 Form Components
| Component | Description |
|-----------|-------------|
| `FormInput` | Text input with label and error |
| `FormSelect` | Dropdown select |
| `FormDatePicker` | Date/time picker |
| `FormCheckbox` | Checkbox with label |
| `FormTextarea` | Multi-line text input |
| `FileUpload` | File upload with drag & drop |
| `PasswordInput` | Password with strength indicator |
| `SearchInput` | Search with debounce |

### 5.4 Feedback Components
| Component | Description |
|-----------|-------------|
| `Toast` | Success/error notifications |
| `Alert` | Inline alerts |
| `Modal` | Dialog/modal windows |
| `ConfirmDialog` | Confirmation dialog |
| `LoadingSpinner` | Loading indicator |
| `ProgressBar` | Progress indicator |

---

## 6. State Management

### 6.1 Server State (React Query)
```typescript
// Queries
useUser()              // Current user
useUsers(filters)      // User list
useWeighSlips(filters) // Weigh slips list
useSites()             // Construction sites
// etc.

// Mutations
useLogin()
useRegister()
useUpdateProfile()
useCreateWeighSlip()
useAssignSlip()
// etc.
```

### 6.2 Client State
```typescript
// Auth Context
- isAuthenticated: boolean
- user: User | null
- tokens: Tokens | null
- login(), logout(), refreshToken()

// UI Context
- sidebarCollapsed: boolean
- theme: 'light' | 'dark'
- toggleSidebar(), setTheme()
```

---

## 7. API Integration

### 7.1 HTTP Client Setup
```typescript
// lib/api.ts
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' }
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor - handle 401, refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try refresh token
      // If fails, logout
    }
    return Promise.reject(error);
  }
);
```

### 7.2 API Response Types
```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: {
    page: number;
    per_page: number;
    total_items: number;
    total_pages: number;
  };
}

interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
```

---

## 8. Security Requirements

### 8.1 Authentication
- JWT stored in httpOnly cookies (preferred) or secure localStorage
- Automatic token refresh before expiration
- Logout on token invalidation
- Protected routes redirect to login

### 8.2 Authorization
- Route-level protection based on roles
- Component-level conditional rendering
- API calls include proper authorization headers

### 8.3 Input Validation
- Client-side validation with Zod
- XSS prevention (React handles by default)
- CSRF protection (if using cookies)

---

## 9. Performance Requirements

### 9.1 Loading States
- Skeleton loaders for all data fetching
- Optimistic updates for mutations
- Debounced search inputs (300ms)

### 9.2 Caching
- React Query cache with appropriate stale times
- Static page pre-rendering where possible

### 9.3 Bundle Size
- Code splitting per route
- Lazy loading for non-critical components
- Image optimization with next/image

---

## 10. Error Handling

### 10.1 API Errors
- Display user-friendly error messages
- Log errors to console (dev) / monitoring (prod)
- Retry mechanism for network errors

### 10.2 Form Errors
- Field-level error display
- Form-level error summary
- Clear errors on input change

### 10.3 Global Errors
- Error boundary for React errors
- 404 page for unknown routes
- 500 error page for server errors

---

## 11. Testing Requirements

### 11.1 Unit Tests
- Component rendering tests
- Hook tests
- Utility function tests

### 11.2 Integration Tests
- Form submission flows
- Authentication flows
- Data table interactions

### 11.3 E2E Tests (Optional)
- Critical user journeys
- Login → Dashboard → Action flows

---

## 12. Accessibility Requirements

- Keyboard navigation support
- Screen reader compatibility
- Focus management
- Color contrast compliance
- ARIA labels where needed
- Skip links for navigation

---

## 13. Internationalization (Future)

- Prepared for i18n with next-intl or similar
- All text in translation files
- Date/number formatting locale-aware

---

## 14. Environment Variables

```env
# API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# App
NEXT_PUBLIC_APP_NAME=Landfill Management System
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Optional
NEXT_PUBLIC_SENTRY_DSN=
```

---

**End of Frontend PRD**
