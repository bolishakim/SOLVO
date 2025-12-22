# Project Description
## Landfill Management System - Automated Waste Tracking

---

## 1. Problem Statement

### Current Situation
An Austrian waste management company currently uses **manual Excel-based processes** to track construction site waste disposal:

**Pain Points**:
- ⚠️ PDFs arrive via email from landfill companies (Saubermacher, etc.)
- ⚠️ Staff manually reads each PDF page
- ⚠️ Staff manually types data into Excel spreadsheet
- ⚠️ Time-consuming: ~5-10 minutes per document
- ⚠️ High error rate from manual data entry
- ⚠️ No tracking of who entered what data
- ⚠️ Difficult to find specific records
- ⚠️ No connection between invoices and weigh slips
- ⚠️ Hazardous waste documentation stored separately as paper/PDF

### Business Impact
- 📉 Inefficient use of staff time
- 📉 Delayed reporting to construction site managers
- 📉 Risk of compliance issues with hazardous waste tracking
- 📉 No audit trail for data changes
- 📉 Difficult to generate reports for multiple projects

---

## 2. Proposed Solution

### High-Level Overview
Build a **multi-workflow web application** that:
1. Accepts PDF uploads from landfill companies
2. Uses **LLM (AI)** to automatically extract data from PDFs
3. Stores data in structured database
4. Allows users to review, correct, and assign data to construction sites
5. Provides Excel export in the same format they currently use
6. Tracks all user actions for compliance

### Technology Approach
- **AI-Powered Extraction**: Use GPT-4 Vision or Claude 3 Opus to read PDF pages
- **Multi-Schema Database**: PostgreSQL with separate schemas for core app and each workflow
- **Role-Based Access**: Users only see their assigned construction sites
- **Audit Trail**: Complete logging of all data changes
- **Familiar Output**: Export to Excel matching current template

---

## 3. User Roles

### Admin
- Can see ALL construction sites and data
- Can assign sites to users
- Can manage master data (companies, materials, users)
- Full system access

### Standard User
- Can see ONLY assigned construction sites
- Can upload PDFs for their projects
- Can review and correct extracted data
- Can assign weigh slips to their sites
- Can export data for their sites

### Viewer (Read-Only)
- Can view data for assigned sites
- Cannot upload or modify data
- Can export reports

---

## 4. Current Manual Workflow

### Step-by-Step Process (Current)
1. Landfill company emails PDF invoice/receipt package
2. PDF contains multiple pages:
   - Wiegeschein (weigh slip) pages - weight and material data
   - Begleitschein (hazardous slip) pages - for dangerous materials
   - Invoice page - billing information
   - Other administrative pages
3. Staff opens PDF and Excel spreadsheet side-by-side
4. For each Wiegeschein page, staff manually types:
   - Date
   - Construction site (Baustelle)
   - Material key number (Schlüsselnummer)
   - Material name
   - Landfill company
   - Location
   - Weight in kg
   - Invoice number
   - Delivery slip number
   - Hazardous yes/no
5. If hazardous, staff prints/saves the Begleitschein page separately
6. Repeat for all pages
7. Save Excel file
8. Send report to construction site manager

**Time**: 30-60 minutes per multi-page PDF

---

## 5. Automated Workflow (New System)

### Step-by-Step Process (Automated)
1. User logs into web app
2. User selects "Upload PDF" 
3. System saves PDF and starts AI processing
4. AI analyzes each page:
   - **Wiegeschein page** → Extract data → Save to `weigh_slips` table
   - **Begleitschein page** → Extract data + capture page as image → Save to `hazardous_slips` table
   - **Other pages** → Ignore or flag for review
5. User sees list of extracted records with status "PENDING"
6. User reviews data, makes corrections if needed
7. User assigns records to construction site
8. User can export to Excel anytime
9. System logs all actions (who, when, what changed)

**Time**: 5-10 minutes per PDF (mostly review time)

**Time Saved**: 80-90%

---

## 6. Key Features

### Phase 1: Core Automation (Weeks 2-3, Milestone 1)

#### PDF Upload & Extraction
- Drag-and-drop PDF upload
- Batch upload (multiple PDFs)
- Automatic detection of page types (Wiegeschein vs Begleitschein)
- AI extraction of structured data
- Confidence score displayed for each field
- Warning system for pages that couldn't be recognized

#### Data Review & Correction
- List view of all extracted weigh slips
- Filter by: date, site, material, company, hazardous status
- Manual correction capability
- Mark fields as "verified"
- Compare AI extraction with original PDF (side-by-side view)

#### Construction Site Assignment
- Auto-assign based on site number in PDF (if found)
- Manual assignment dropdown
- Bulk assignment (select multiple records)
- Assignment status: PENDING → ASSIGNED

#### Excel Export
- Export filtered data to Excel
- Same format as current template
- One-click download
- Track export history

#### Hazardous Waste Documentation
- Automatic detection of hazardous materials
- Store Begleitschein page as image (base64)
- Display image in UI when viewing record
- Print/save Begleitschein separately if needed

---

### Phase 2: Multi-User & Cloud (Weeks 3-4, Milestone 2)

#### User Management
- Create users with roles (Admin, Standard User, Viewer)
- Assign construction sites to users
- Two-factor authentication (2FA)
- Password reset flow

#### Access Control
- Users see only their assigned sites
- Admins see everything
- Audit log of who accessed what

#### Cloud Deployment
- Hosted on cloud platform
- 3-5 concurrent users supported
- 99% uptime SLA

#### Data Backup
- Automatic daily backups
- Soft delete (data kept for 7 years)
- Admin-only access to deleted records

---

### Phase 3 & 4: Future Enhancements

**Milestone 3** (Q1/2025): Employee Hours Assignment
- Import Excel with employee hours per site
- Link hours to construction sites
- Integrated reporting

**Milestone 4** (Q1-Q2/2025): Invoice Processing
- Extract invoice data from PDFs
- Auto-link invoices to weigh slips
- Invoice overview per site
- Payment tracking

---

## 7. Data Flow Diagram

```
┌─────────────┐
│ PDF Upload  │
└──────┬──────┘
       │
       v
┌─────────────┐
│ File Storage│
└──────┬──────┘
       │
       v
┌─────────────┐
│  LLM Vision │ ←─── GPT-4 or Claude 3
└──────┬──────┘
       │
       v
┌─────────────────────────────┐
│  Page Type Detection        │
├─────────────────────────────┤
│  • Wiegeschein?             │
│  • Begleitschein?           │
│  • Other?                   │
└──────┬──────────────────────┘
       │
       ├─── Wiegeschein ──────> Extract Data ──> weigh_slips table
       │
       └─── Begleitschein ───> Extract Data + Image ──> hazardous_slips table
```

---

## 8. Database Structure (Simplified)

### Core App Schema
- Users, roles, authentication
- Workflows registry
- Audit logs
- Data exports

### Landfill Management Schema
- Construction sites (Baustellen)
- User site assignments (access control)
- Landfill companies (Saubermacher, etc.)
- Landfill locations (Sortierplätze)
- Material types (Schlüsselnummern)
- **Weigh slips (MAIN TABLE)** - extracted Wiegeschein data
- **Hazardous slips** - Begleitschein data + base64 images
- PDF documents (originals)

---

## 9. Example Scenarios

### Scenario 1: Standard User Daily Workflow
1. Maria logs in and sees her 3 assigned construction sites
2. She uploads today's PDF from Saubermacher (15 pages)
3. System extracts 12 weigh slips automatically
4. Maria reviews the data - AI got 11/12 correct
5. She corrects one material type that was misidentified
6. She assigns all 12 slips to "AKH-BT74" construction site
7. She exports Excel for weekly report to site manager
8. Total time: 8 minutes

### Scenario 2: Hazardous Waste Tracking
1. System extracts weigh slip #5 - detects hazardous material
2. AI also finds corresponding Begleitschein page
3. System stores:
   - Begleitschein number: "2922 22 / 9110025448884"
   - Waste code: 31437/44
   - Weight: 5.2 tons
   - Page image (base64)
4. User clicks "View Hazardous Documentation"
5. Original Begleitschein page displays in browser
6. User can print/save for compliance records

### Scenario 3: Admin Oversight
1. Admin logs in and sees ALL sites across company
2. Admin notices site "Project Vienna" has no assigned users
3. Admin assigns user "Johann" to "Project Vienna"
4. Admin reviews audit log - sees Maria corrected 5 records today
5. Admin exports consolidated report for all sites for month

---

## 10. Success Criteria

### Quantitative
- ✅ 90%+ accuracy on AI extraction
- ✅ 80%+ time savings vs manual process
- ✅ Process 100+ PDFs/month
- ✅ Support 10+ concurrent users
- ✅ < 30 seconds processing time per PDF

### Qualitative
- ✅ Users can complete daily tasks without training
- ✅ Zero compliance issues with hazardous waste documentation
- ✅ Construction site managers receive reports faster
- ✅ Easy to find historical records
- ✅ Complete audit trail for all changes

---

## 11. Technical Constraints

### Must-Have
- Run in Austria (data residency)
- German language support in UI
- Support Chrome, Firefox, Safari
- Mobile-responsive (for field use)
- Offline-capable PDF viewing

### Nice-to-Have
- Multi-language support (English)
- Mobile app (iOS/Android)
- Integration with accounting software
- Email notifications for new uploads

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| AI extraction errors | Medium | Manual review + correction UI |
| PDF format changes | High | Retrain/adjust prompts quarterly |
| User adoption | Medium | Training + keep Excel export familiar |
| Data loss | High | Daily backups + soft deletes |
| Slow AI processing | Low | Async processing + status updates |

---

## 13. Project Timeline

### Phase 1: MVP (Weeks 2-3)
- ✅ Database setup
- ✅ User authentication
- ✅ PDF upload
- ✅ AI extraction (Wiegeschein only)
- ✅ Basic review UI
- ✅ Excel export

**Acceptance**: 90%+ successful extractions on test PDFs

### Phase 2: Production (Weeks 3-4)
- ✅ Multi-user support
- ✅ Site access control
- ✅ Hazardous slip handling
- ✅ Cloud deployment
- ✅ 2FA authentication
- ✅ Audit logging

**Acceptance**: 3-5 users can work concurrently

### Phase 3: Enhancements (Q1/2025)
- Hours assignment
- Invoice linking

---

## 14. Future Expansion

### Additional Workflows (Future)
The system is designed as a **multi-workflow platform**:
- Workflow 2: Equipment tracking
- Workflow 3: Employee time tracking
- Workflow 4: Vehicle maintenance logs

Each workflow gets its own database schema and can be developed independently.

---

**End of Project Description**
