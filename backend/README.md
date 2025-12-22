# Landfill Management System - Backend

Multi-workflow backend system for Austrian waste management company.

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 17 with multi-schema architecture
- **ORM**: SQLAlchemy 2.0 (async with asyncpg)
- **Migrations**: Alembic
- **Authentication**: JWT + TOTP (2FA)
- **Python**: 3.11+

## Features

- **Authentication**: JWT-based with access/refresh tokens
- **Two-Factor Authentication**: TOTP-based with backup codes
- **Role-Based Access Control**: Admin, Standard User, Viewer roles
- **Session Management**: Multi-device support, session revocation
- **Audit Logging**: Complete tracking of all user actions
- **Account Security**: Lockout after failed attempts, password reset
- **Rate Limiting**: Per-IP and per-endpoint rate limits
- **Security Headers**: OWASP-compliant security headers

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic settings configuration
│   ├── database.py          # SQLAlchemy async setup
│   │
│   ├── core/                # Core application (auth, users, audit)
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   └── dependencies.py  # FastAPI dependencies
│   │
│   ├── workflows/           # Business workflows
│   │   ├── landfill_mgmt/   # Landfill document management
│   │   └── _template/       # Template for new workflows
│   │
│   ├── shared/              # Shared utilities
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── responses.py     # Response helpers
│   │   ├── security.py      # Password/JWT utilities
│   │   └── validators.py    # Input validators
│   │
│   └── middleware/          # Custom middleware
│       ├── request_id.py    # X-Request-ID tracking
│       ├── security_headers.py  # Security headers
│       └── rate_limit.py    # Rate limiting
│
├── alembic/                 # Database migrations
├── tests/                   # Test suite
│   ├── conftest.py          # Test fixtures
│   ├── core/                # Core module tests
│   └── test_integration.py  # Integration tests
├── scripts/                 # Utility scripts
│   └── create_admin.py      # Admin user creation
└── docker-compose.yml       # Local development services
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### 2. Clone and Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 3. Start Database

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Verify it's running
docker-compose ps
```

### 4. Run Migrations

```bash
# Apply all migrations
alembic upgrade head
```

### 5. Create Admin User

```bash
# Interactive mode
python scripts/create_admin.py

# Or with arguments
python scripts/create_admin.py --username admin --email admin@example.com
```

### 6. Run Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m app.main
```

### 7. Access API

- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health
- **DB Health**: http://localhost:8000/health/db

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | User login |
| POST | `/logout` | User logout |
| POST | `/refresh-token` | Refresh access token |
| GET | `/session/validate` | Validate current session |
| POST | `/change-password` | Change password |
| POST | `/forgot-password` | Request password reset |
| POST | `/reset-password` | Reset password with token |
| GET | `/me` | Get current user profile |
| PUT | `/me` | Update current user profile |

### Session Management (`/api/v1/auth/sessions`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sessions` | List user sessions |
| DELETE | `/sessions/{id}` | Revoke specific session |
| POST | `/sessions/revoke-all` | Revoke all sessions |

### Two-Factor Authentication (`/api/v1/auth/2fa`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/2fa/setup` | Initiate 2FA setup |
| POST | `/2fa/verify` | Verify and enable 2FA |
| POST | `/2fa/disable` | Disable 2FA |
| GET | `/2fa/status` | Get 2FA status |
| POST | `/2fa/backup-codes/regenerate` | Regenerate backup codes |
| POST | `/login/2fa` | Complete login with TOTP |
| POST | `/login/backup-code` | Complete login with backup code |

### Admin (`/api/v1/admin`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get user by ID |
| PUT | `/users/{id}` | Update user |
| DELETE | `/users/{id}` | Deactivate user |
| GET | `/roles` | List all roles |
| GET | `/users/{id}/roles` | Get user roles |
| POST | `/users/{id}/roles` | Assign role |
| DELETE | `/users/{id}/roles/{role_id}` | Remove role |
| GET | `/stats` | Get system statistics |
| GET | `/audit-logs` | List audit logs |
| GET | `/audit-logs/stats` | Audit statistics |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/core/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest -m "not integration"

# Run only integration tests
pytest -m integration
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Code Quality

```bash
# Format code
black app tests
ruff check app tests --fix

# Type check
mypy app
```

## Database Schemas

| Schema | Purpose |
|--------|---------|
| `core_app` | Authentication, users, sessions, audit logs, roles |
| `landfill_mgmt` | Construction sites, weigh slips, hazardous slips |

### Core Models

- **User**: User accounts with authentication
- **Role**: User roles (Admin, Standard User, Viewer)
- **UserRole**: User-role assignments
- **UserSession**: Active sessions
- **TwoFactorAuth**: 2FA configuration
- **PasswordResetToken**: Password reset tokens
- **AuditLog**: Audit trail

## Environment Variables

See `.env.example` for all available configuration options.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `JWT_SECRET_KEY` | JWT signing key (min 32 chars) | Generate with `openssl rand -hex 32` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `ACCOUNT_LOCKOUT_ATTEMPTS` | `5` | Failed attempts before lockout |
| `ACCOUNT_LOCKOUT_MINUTES` | `15` | Lockout duration |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

## API Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

## Security Features

### Rate Limiting

- General endpoints: 60 requests/minute per IP
- Authentication endpoints: 10 requests/minute per IP
- Returns `429 Too Many Requests` with `Retry-After` header

### Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (in production)

### Account Lockout

- Account locked after 5 failed login attempts
- Auto-unlock after 15 minutes
- Password reset clears lockout

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Production Deployment

### Checklist

1. Set `DEBUG=false`
2. Generate secure `JWT_SECRET_KEY`
3. Configure proper `DATABASE_URL`
4. Set up HTTPS (for HSTS)
5. Configure proper `CORS_ORIGINS`
6. Set up database backups
7. Configure logging/monitoring

### Running with Gunicorn

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## License

Proprietary - All rights reserved.
