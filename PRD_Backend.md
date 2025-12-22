# Backend Product Requirements Document (PRD)
## Landfill Management System - Multi-Workflow Application

---

## 1. Project Overview

**Purpose**: Build a multi-workflow backend system for Austrian waste management company to digitize manual PDF data extraction and construction site tracking.

**Target Users**: Construction site managers, waste management operators, system administrators

**Tech Stack**:
- **Backend**: Python (FastAPI or Flask)
- **Database**: PostgreSQL (multi-schema architecture)
- **LLM Integration**: OpenAI GPT-4 Vision / Claude 3 Opus
- **Authentication**: JWT + 2FA (TOTP)
- **File Storage**: Local filesystem or S3-compatible storage

---

## 2. Database Architecture

### Schema Structure
```
├── core_app (main application)
│   ├── users, roles, user_roles
│   ├── two_factor_auth, user_sessions
│   ├── workflows, audit_logs
│   └── data_exports
│
└── landfill_mgmt (workflow 1)
    ├── construction_sites, user_construction_sites
    ├── landfill_companies, landfill_locations
    ├── material_types, pdf_documents
    ├── weigh_slips (main table)
    └── hazardous_slips (with base64 images)
```

**Key Design Principles**:
- Complete separation between core app and workflows
- Each workflow = separate schema
- Easy to add new workflows without touching existing ones
- All tables track `created_by` and `updated_by`

---

## 3. Core Features

### 3.1 Authentication & Authorization

**Endpoints Required**:
```
POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/refresh-token
POST /auth/2fa/setup
POST /auth/2fa/verify
GET  /auth/session/validate
```

**Access Control Logic**:
- **Admin Role**: Access ALL construction sites and data
- **Standard User**: Access ONLY assigned construction sites (via `user_construction_sites` table)
- **Viewer**: Read-only access to assigned sites

**Implementation**:
```python
# Example access control
def get_user_accessible_sites(user_id: int, role: str):
    if role == "Admin":
        return "SELECT * FROM landfill_mgmt.construction_sites"
    else:
        return """
            SELECT cs.* FROM landfill_mgmt.construction_sites cs
            INNER JOIN landfill_mgmt.user_construction_sites ucs 
            ON cs.site_id = ucs.site_id
            WHERE ucs.user_id = :user_id
        """
```

---

### 3.2 Workflow 1: Landfill Document Management

#### PDF Upload & Processing

**Endpoints**:
```
POST   /landfill/documents/upload
GET    /landfill/documents
GET    /landfill/documents/{document_id}
DELETE /landfill/documents/{document_id}
```

**Upload Flow**:
1. User uploads PDF → Save to storage → Create record in `pdf_documents`
2. Set status: `UPLOADED`
3. Trigger async processing job
4. LLM extracts data from two PDF page types:
   - **Wiegeschein** (Weigh Slip) → Extract to `weigh_slips` table
   - **Begleitschein** (Hazardous Slip) → Extract to `hazardous_slips` + store base64 image
5. Update status: `COMPLETED` or `FAILED`

**LLM Extraction Requirements**:
- Use GPT-4 Vision or Claude 3 Opus with vision capabilities
- Extract structured data from PDF pages
- For hazardous slips: Convert page to base64 PNG/JPEG and store in `page_image_base64` column
- Handle multi-page PDFs (one PDF may contain multiple weigh slips and hazardous slips)

---

#### Weigh Slips Management

**Endpoints**:
```
GET    /landfill/weigh-slips              # List (filtered by user access)
GET    /landfill/weigh-slips/{slip_id}    # Get single
POST   /landfill/weigh-slips              # Manual entry
PUT    /landfill/weigh-slips/{slip_id}    # Update/correct
DELETE /landfill/weigh-slips/{slip_id}    # Soft delete
POST   /landfill/weigh-slips/{slip_id}/assign  # Assign to construction site
```

**Query Filters**:
- Date range (delivery_date)
- Construction site
- Material type
- Hazardous vs non-hazardous
- Assignment status (PENDING, ASSIGNED)
- Company/Location

**Assign to Site Logic**:
```python
PUT /landfill/weigh-slips/{slip_id}/assign
Body: { "site_id": 123 }

# Update weigh slip
UPDATE weigh_slips 
SET site_id = :site_id, 
    assignment_status = 'ASSIGNED',
    updated_by = :current_user_id
WHERE slip_id = :slip_id
```

---

#### Hazardous Slips

**Endpoints**:
```
GET /landfill/hazardous-slips
GET /landfill/hazardous-slips/{slip_id}
GET /landfill/hazardous-slips/{hazardous_slip_id}/image  # Return base64 or serve image
```

**Image Retrieval**:
```python
GET /landfill/hazardous-slips/{hazardous_slip_id}/image

# Return base64 string that frontend can use:
# <img src="data:image/png;base64,{base64_string}" />
```

---

### 3.3 Construction Sites Management

**Endpoints**:
```
GET    /landfill/construction-sites
POST   /landfill/construction-sites
PUT    /landfill/construction-sites/{site_id}
DELETE /landfill/construction-sites/{site_id}
POST   /landfill/construction-sites/{site_id}/assign-user
DELETE /landfill/construction-sites/{site_id}/unassign-user
```

**User Assignment**:
```python
POST /landfill/construction-sites/{site_id}/assign-user
Body: { "user_id": 456 }

# Insert into user_construction_sites table
INSERT INTO user_construction_sites (user_id, site_id, assigned_by)
VALUES (:user_id, :site_id, :current_admin_user_id)
```

---

### 3.4 Master Data Management

**Companies & Locations**:
```
GET  /landfill/companies
POST /landfill/companies
GET  /landfill/locations
POST /landfill/locations
```

**Material Types**:
```
GET  /landfill/material-types
POST /landfill/material-types
PUT  /landfill/material-types/{material_id}
```

---

### 3.5 Data Export

**Endpoints**:
```
POST /landfill/export/excel
POST /landfill/export/pdf
GET  /landfill/exports/{export_id}/download
```

**Excel Export Logic**:
- Query weigh_slips based on user access + filters
- Generate Excel file matching the provided template structure:
  - Columns: Datum, Baustelle, Schlüsselnummer, Materialart, Firma, Standort, Masse in kg, Rechnungsnummer, Lieferscheinnummer, Gefährlich/Nicht Gefährlich
- Store file path in `data_exports` table
- Return download URL

---

### 3.6 Audit Logging

**Auto-log these actions**:
- User login/logout
- Create/update/delete weigh slips
- Assign weigh slip to construction site
- Create/update construction sites
- Data exports
- User assignments to sites

**Implementation**:
```python
# After every significant action
insert_audit_log(
    user_id=current_user.id,
    workflow_schema="landfill_mgmt",
    action_type="UPDATE",
    entity_type="WEIGH_SLIP",
    entity_id=slip_id,
    changes={"old": old_values, "new": new_values},
    ip_address=request.client.host
)
```

---

## 4. LLM Integration Specifications

### PDF Page Type Detection

**Prompt Pattern**:
```
Analyze this PDF page and determine its type:
1. "Wiegeschein" (Weigh Slip) - contains: Wiegeschein number, weight measurements, waste material
2. "Begleitschein für gefährlichen Abfall" (Hazardous Waste Slip) - contains: "BEGLEITSCHEIN FÜR GEFÄHRLICHEN ABFALL" header
3. "Other" - any other document type

Return JSON: {"page_type": "wiegeschein|begleitschein|other"}
```

### Wiegeschein Extraction

**Prompt Pattern**:
```
Extract the following data from this Wiegeschein (weigh slip):

Required fields:
- slip_number: Wiegeschein number (e.g., "20192560")
- delivery_date: Date (format: YYYY-MM-DD)
- net_weight_kg: Net weight in kg (Netto)
- company_name: Landfill company name
- location_name: Sortierplatz location
- material_code: Art.Nr. (e.g., "330053")
- material_name: Bezeichnung (material description)
- onorm_code: Önorm/Spez. code
- is_hazardous: Boolean (look for "gef." marker)

Optional fields:
- vehicle_license_plate: Fahrzeug
- transporter_name: Transporteur
- waste_origin_address: Absendeort address

Return valid JSON only.
```

### Begleitschein Extraction + Image

**Process**:
1. Detect it's a hazardous slip page
2. Extract data:
```
Required fields:
- begleitschein_number: Official tracking number
- waste_code: Abfallcode (e.g., "31437")
- specification: Spez. (e.g., "44")
- mass_kg: Masse in kg
- disposal_method: R/D code (e.g., "D15")
- transport_date: Date
- transporter_company: Übergebeber company
- receiver_company: Übernehmer company

Return JSON.
```
3. Convert entire page to base64 image (PNG or JPEG)
4. Store both extracted data + base64 in `hazardous_slips` table

---

## 5. Non-Functional Requirements

### Performance
- PDF processing: < 30 seconds per document (async)
- API response time: < 500ms for data queries
- Support 50 concurrent users

### Security
- All passwords hashed with bcrypt (12 rounds)
- JWT tokens expire after 1 hour
- Refresh tokens expire after 7 days
- 2FA required for Admin role
- Rate limiting: 100 requests/minute per user

### Data Retention
- Audit logs: Keep 2 years
- Exports: Auto-delete after 7 days
- Soft deletes: Keep indefinitely (for compliance)

### File Storage
- PDF documents: Keep original files
- Max file size: 50MB per PDF
- Supported formats: PDF only

---

## 6. API Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid site_id provided",
    "details": { ... }
  }
}
```

### Pagination
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 150,
    "total_pages": 8
  }
}
```

---

## 7. Development Priorities

### Phase 1 (Core - Weeks 1-2)
1. Setup database schemas
2. User authentication + 2FA
3. PDF upload + storage
4. LLM integration for Wiegeschein extraction
5. Basic CRUD for weigh_slips

### Phase 2 (Complete Workflow - Weeks 2-3)
6. Construction site management
7. User access control (user_construction_sites)
8. Assign weigh slips to sites
9. Hazardous slip extraction + base64 storage
10. Excel export functionality

### Phase 3 (Polish - Week 3)
11. Audit logging
12. Master data management (companies, materials)
13. Error handling + validation
14. Testing + bug fixes

---

## 8. Testing Requirements

### Unit Tests
- Database operations (CRUD)
- Access control logic
- LLM extraction parsing

### Integration Tests
- Complete PDF upload → extraction → assignment flow
- User authentication + authorization
- Data export generation

### Test Data
- Sample PDFs provided (Wiegeschein + Begleitschein)
- Test users with different roles
- Sample construction sites

---

## 9. Error Handling

**Common Error Cases**:
- PDF upload fails → Return error, cleanup partial files
- LLM extraction fails → Mark document as FAILED, allow manual entry
- User tries to access unauthorized site → Return 403 Forbidden
- Invalid data in update → Return 400 with validation errors
- Database connection fails → Return 503 Service Unavailable

---

## 10. Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/landfill_db

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# LLM
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# File Storage
UPLOAD_DIR=/path/to/uploads
MAX_FILE_SIZE_MB=50

# Application
DEBUG=false
CORS_ORIGINS=http://localhost:3000
```

---

## 11. API Documentation

Use **OpenAPI/Swagger** for auto-generated API documentation.

Access at: `GET /docs`

---

**End of PRD**
