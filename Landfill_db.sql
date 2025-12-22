-- ============================================================================
-- LANDFILL MANAGEMENT SYSTEM - DATABASE SCHEMA
-- Multi-Workflow Application for Waste Material Management
-- Company: Austrian Waste Management Company
-- ============================================================================

-- ============================================================================
-- SCHEMA 1: CORE APPLICATION
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS core_app;

-- Users Table
CREATE TABLE core_app.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE core_app.users IS 'System users with authentication credentials';
COMMENT ON COLUMN core_app.users.password_hash IS 'Bcrypt or Argon2 hashed password';

-- Roles Table
CREATE TABLE core_app.roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE core_app.roles IS 'User roles for access control';

-- Insert default roles
INSERT INTO core_app.roles (role_name, description) VALUES
('Admin', 'Full system access - can see all projects and data'),
('Standard User', 'Limited access - can only see assigned projects'),
('Viewer', 'Read-only access to assigned projects');

-- User Roles (Many-to-Many)
CREATE TABLE core_app.user_roles (
    user_id INTEGER NOT NULL REFERENCES core_app.users(user_id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES core_app.roles(role_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON TABLE core_app.user_roles IS 'Assignment of roles to users';

-- Two Factor Authentication
CREATE TABLE core_app.two_factor_auth (
    tfa_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES core_app.users(user_id) ON DELETE CASCADE,
    secret_key VARCHAR(255) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE core_app.two_factor_auth IS 'Two-factor authentication settings per user';
COMMENT ON COLUMN core_app.two_factor_auth.secret_key IS 'Encrypted TOTP secret key';

-- User Sessions
CREATE TABLE core_app.user_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES core_app.users(user_id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

COMMENT ON TABLE core_app.user_sessions IS 'Active user sessions for authentication';

CREATE INDEX idx_user_sessions_token ON core_app.user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON core_app.user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires ON core_app.user_sessions(expires_at);

-- Workflows Registry
CREATE TABLE core_app.workflows (
    workflow_id SERIAL PRIMARY KEY,
    workflow_name VARCHAR(100) NOT NULL,
    workflow_code VARCHAR(50) NOT NULL UNIQUE,
    schema_name VARCHAR(50) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE core_app.workflows IS 'Registry of available workflows in the system';

-- Insert default workflow
INSERT INTO core_app.workflows (workflow_name, workflow_code, schema_name) VALUES
('Landfill Document Management', 'landfill_mgmt', 'landfill_mgmt');

-- Audit Logs
CREATE TABLE core_app.audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES core_app.users(user_id) ON DELETE SET NULL,
    workflow_schema VARCHAR(50),
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(100),
    changes JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE core_app.audit_logs IS 'System-wide audit trail for all user actions';
COMMENT ON COLUMN core_app.audit_logs.changes IS 'JSON object containing old and new values';

CREATE INDEX idx_audit_logs_user_id ON core_app.audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON core_app.audit_logs(created_at);
CREATE INDEX idx_audit_logs_entity ON core_app.audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_workflow ON core_app.audit_logs(workflow_schema);

-- Data Exports
CREATE TABLE core_app.data_exports (
    export_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES core_app.users(user_id) ON DELETE CASCADE,
    workflow_schema VARCHAR(50) NOT NULL,
    export_type VARCHAR(20) NOT NULL CHECK (export_type IN ('EXCEL', 'PDF', 'CSV')),
    file_path TEXT NOT NULL,
    filters_applied JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE core_app.data_exports IS 'Track exported files for download and cleanup';

CREATE INDEX idx_data_exports_user_id ON core_app.data_exports(user_id);
CREATE INDEX idx_data_exports_created_at ON core_app.data_exports(created_at);
CREATE INDEX idx_data_exports_expires_at ON core_app.data_exports(expires_at);


-- ============================================================================
-- SCHEMA 2: LANDFILL MANAGEMENT WORKFLOW
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS landfill_mgmt;

-- Construction Sites
CREATE TABLE landfill_mgmt.construction_sites (
    site_id SERIAL PRIMARY KEY,
    site_number VARCHAR(50) NOT NULL,
    site_name VARCHAR(200) NOT NULL,
    client_name VARCHAR(200),
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES core_app.users(user_id) ON DELETE SET NULL
);

COMMENT ON TABLE landfill_mgmt.construction_sites IS 'Construction sites (Baustellen) where waste is generated';
COMMENT ON COLUMN landfill_mgmt.construction_sites.site_number IS 'Site number (Kst. number) e.g., 1045';

CREATE UNIQUE INDEX idx_construction_sites_number ON landfill_mgmt.construction_sites(site_number) WHERE is_active = TRUE;
CREATE INDEX idx_construction_sites_name ON landfill_mgmt.construction_sites(site_name);
CREATE INDEX idx_construction_sites_created_by ON landfill_mgmt.construction_sites(created_by);

-- User Construction Sites (Access Control)
CREATE TABLE landfill_mgmt.user_construction_sites (
    user_id INTEGER NOT NULL REFERENCES core_app.users(user_id) ON DELETE CASCADE,
    site_id INTEGER NOT NULL REFERENCES landfill_mgmt.construction_sites(site_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES core_app.users(user_id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, site_id)
);

COMMENT ON TABLE landfill_mgmt.user_construction_sites IS 'User access control - which users can see which construction sites. Admin role bypasses this.';

CREATE INDEX idx_user_construction_sites_user ON landfill_mgmt.user_construction_sites(user_id);
CREATE INDEX idx_user_construction_sites_site ON landfill_mgmt.user_construction_sites(site_id);

-- Landfill Companies
CREATE TABLE landfill_mgmt.landfill_companies (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landfill_mgmt.landfill_companies IS 'Waste management companies (e.g., Saubermacher)';
COMMENT ON COLUMN landfill_mgmt.landfill_companies.tax_id IS 'UID number e.g., ATU 64541277';

CREATE INDEX idx_landfill_companies_name ON landfill_mgmt.landfill_companies(company_name);

-- Landfill Locations
CREATE TABLE landfill_mgmt.landfill_locations (
    location_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES landfill_mgmt.landfill_companies(company_id) ON DELETE CASCADE,
    location_name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landfill_mgmt.landfill_locations IS 'Specific landfill locations (Sortierplatz) e.g., Sortierplatz Klosterneuburg';

CREATE INDEX idx_landfill_locations_company ON landfill_mgmt.landfill_locations(company_id);
CREATE INDEX idx_landfill_locations_name ON landfill_mgmt.landfill_locations(location_name);

-- Material Types
CREATE TABLE landfill_mgmt.material_types (
    material_id SERIAL PRIMARY KEY,
    key_number VARCHAR(50) NOT NULL UNIQUE,
    material_name VARCHAR(255) NOT NULL,
    onorm_code VARCHAR(50),
    is_hazardous BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landfill_mgmt.material_types IS 'Types of waste materials (Schlüsselnummer)';
COMMENT ON COLUMN landfill_mgmt.material_types.key_number IS 'Material key number e.g., 330053, 20050';
COMMENT ON COLUMN landfill_mgmt.material_types.onorm_code IS 'ÖNORM specification code e.g., 17202/1';

CREATE INDEX idx_material_types_key_number ON landfill_mgmt.material_types(key_number);
CREATE INDEX idx_material_types_hazardous ON landfill_mgmt.material_types(is_hazardous);

-- Insert common material types
INSERT INTO landfill_mgmt.material_types (key_number, material_name, onorm_code, is_hazardous) VALUES
('330053', 'Bau- und Abbruchholz - Thermisch', '17202/1', FALSE),
('20050', 'Baustellenmischabfälle', '91206', FALSE),
('40020', 'Sperrmüll', '91401', FALSE),
('10180', 'PVC-Abfälle', '57116', FALSE),
('10020', 'Gewerbemüll', '91101', FALSE),
('112267', 'Mischung aus Glas- und Steinwolle', '31437/44', TRUE);

-- PDF Documents
CREATE TABLE landfill_mgmt.pdf_documents (
    document_id SERIAL PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER NOT NULL REFERENCES core_app.users(user_id) ON DELETE SET NULL,
    processing_status VARCHAR(50) DEFAULT 'UPLOADED' CHECK (processing_status IN ('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED')),
    extraction_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE landfill_mgmt.pdf_documents IS 'Uploaded PDF documents for processing';
COMMENT ON COLUMN landfill_mgmt.pdf_documents.file_hash IS 'SHA-256 hash for duplicate detection';

CREATE INDEX idx_pdf_documents_uploaded_by ON landfill_mgmt.pdf_documents(uploaded_by);
CREATE INDEX idx_pdf_documents_status ON landfill_mgmt.pdf_documents(processing_status);
CREATE INDEX idx_pdf_documents_hash ON landfill_mgmt.pdf_documents(file_hash);

-- Weigh Slips (Main Table)
CREATE TABLE landfill_mgmt.weigh_slips (
    slip_id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES landfill_mgmt.pdf_documents(document_id) ON DELETE SET NULL,
    slip_number VARCHAR(100) NOT NULL,
    site_id INTEGER REFERENCES landfill_mgmt.construction_sites(site_id) ON DELETE SET NULL,
    company_id INTEGER NOT NULL REFERENCES landfill_mgmt.landfill_companies(company_id) ON DELETE RESTRICT,
    location_id INTEGER NOT NULL REFERENCES landfill_mgmt.landfill_locations(location_id) ON DELETE RESTRICT,
    material_id INTEGER NOT NULL REFERENCES landfill_mgmt.material_types(material_id) ON DELETE RESTRICT,
    delivery_date DATE NOT NULL,
    net_weight_kg DECIMAL(10, 2) NOT NULL,
    invoice_number VARCHAR(100),
    is_hazardous BOOLEAN DEFAULT FALSE,
    vehicle_license_plate VARCHAR(50),
    transporter_name VARCHAR(255),
    waste_origin_address TEXT,
    assignment_status VARCHAR(50) DEFAULT 'PENDING' CHECK (assignment_status IN ('PENDING', 'ASSIGNED')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core_app.users(user_id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES core_app.users(user_id) ON DELETE SET NULL
);

COMMENT ON TABLE landfill_mgmt.weigh_slips IS 'Main table - Weigh slips (Wiegescheine) extracted from PDFs';
COMMENT ON COLUMN landfill_mgmt.weigh_slips.slip_number IS 'Lieferscheinnummer from PDF';
COMMENT ON COLUMN landfill_mgmt.weigh_slips.net_weight_kg IS 'Masse in kg (net weight)';
COMMENT ON COLUMN landfill_mgmt.weigh_slips.assignment_status IS 'Whether slip has been assigned to a construction site';

CREATE INDEX idx_weigh_slips_slip_number ON landfill_mgmt.weigh_slips(slip_number);
CREATE INDEX idx_weigh_slips_site_id ON landfill_mgmt.weigh_slips(site_id);
CREATE INDEX idx_weigh_slips_delivery_date ON landfill_mgmt.weigh_slips(delivery_date);
CREATE INDEX idx_weigh_slips_company ON landfill_mgmt.weigh_slips(company_id);
CREATE INDEX idx_weigh_slips_material ON landfill_mgmt.weigh_slips(material_id);
CREATE INDEX idx_weigh_slips_hazardous ON landfill_mgmt.weigh_slips(is_hazardous);
CREATE INDEX idx_weigh_slips_created_by ON landfill_mgmt.weigh_slips(created_by);
CREATE INDEX idx_weigh_slips_status ON landfill_mgmt.weigh_slips(assignment_status);

-- Composite index for common query pattern
CREATE INDEX idx_weigh_slips_site_date ON landfill_mgmt.weigh_slips(site_id, delivery_date) WHERE site_id IS NOT NULL;

-- Hazardous Slips (Begleitschein für gefährlichen Abfall)
CREATE TABLE landfill_mgmt.hazardous_slips (
    hazardous_slip_id SERIAL PRIMARY KEY,
    slip_id INTEGER NOT NULL REFERENCES landfill_mgmt.weigh_slips(slip_id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES landfill_mgmt.pdf_documents(document_id) ON DELETE SET NULL,
    begleitschein_number VARCHAR(100) NOT NULL,
    waste_code VARCHAR(20),
    specification VARCHAR(20),
    mass_kg DECIMAL(10, 2),
    disposal_method VARCHAR(10),
    transporter_company VARCHAR(255),
    transporter_bs_number VARCHAR(100),
    receiver_company VARCHAR(255),
    receiver_id_number VARCHAR(100),
    transport_date DATE,
    transport_type VARCHAR(5),
    page_image_base64 TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core_app.users(user_id) ON DELETE SET NULL
);

COMMENT ON TABLE landfill_mgmt.hazardous_slips IS 'Hazardous waste documentation (Begleitschein) with base64 image storage';
COMMENT ON COLUMN landfill_mgmt.hazardous_slips.begleitschein_number IS 'Official hazardous waste tracking number';
COMMENT ON COLUMN landfill_mgmt.hazardous_slips.waste_code IS 'Abfallcode e.g., 31437';
COMMENT ON COLUMN landfill_mgmt.hazardous_slips.specification IS 'Spez. code e.g., 44';
COMMENT ON COLUMN landfill_mgmt.hazardous_slips.disposal_method IS 'R/D code e.g., D15';
COMMENT ON COLUMN landfill_mgmt.hazardous_slips.transport_type IS '1=Road, 2=Rail, 3=Water, 4=Air, 5=Combined';
COMMENT ON COLUMN landfill_mgmt.hazardous_slips.page_image_base64 IS 'Base64 encoded image of the hazardous slip page for display in frontend';

CREATE INDEX idx_hazardous_slips_slip_id ON landfill_mgmt.hazardous_slips(slip_id);
CREATE INDEX idx_hazardous_slips_begleitschein ON landfill_mgmt.hazardous_slips(begleitschein_number);
CREATE INDEX idx_hazardous_slips_created_by ON landfill_mgmt.hazardous_slips(created_by);


-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON core_app.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_construction_sites_updated_at BEFORE UPDATE ON landfill_mgmt.construction_sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_weigh_slips_updated_at BEFORE UPDATE ON landfill_mgmt.weigh_slips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample landfill company (Saubermacher)
INSERT INTO landfill_mgmt.landfill_companies (company_name, tax_id, address, city, postal_code, phone, email) VALUES
('Saubermacher Bau Recycling & Entsorgung GmbH', 'ATU 64541277', 'Oberlaaer Straße 272', 'Wien', '1230', '+43 59 800 7800', 'office@saubermacher-baurecycling.at');

-- Insert sample landfill locations
INSERT INTO landfill_mgmt.landfill_locations (company_id, location_name, address, city, postal_code) VALUES
(1, 'Sortierplatz Klosterneuburg', 'Donaustraße 88', 'Klosterneuburg', '3400'),
(1, 'Sortierplatz Leopoldsdorf', 'Himbergerstraße 38', 'Leopoldsdorf bei Wien', '2333'),
(1, 'Sortierplatz Oberlaa', 'Oberlaaer Straße 272', 'Wien', '1230');


-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for users to see only their accessible weigh slips
CREATE OR REPLACE VIEW landfill_mgmt.v_user_accessible_weigh_slips AS
SELECT 
    ws.*,
    cs.site_number,
    cs.site_name,
    cs.client_name,
    mt.key_number,
    mt.material_name,
    mt.onorm_code,
    lc.company_name,
    ll.location_name,
    u.username as created_by_username,
    u.first_name || ' ' || u.last_name as created_by_name
FROM landfill_mgmt.weigh_slips ws
LEFT JOIN landfill_mgmt.construction_sites cs ON ws.site_id = cs.site_id
INNER JOIN landfill_mgmt.material_types mt ON ws.material_id = mt.material_id
INNER JOIN landfill_mgmt.landfill_companies lc ON ws.company_id = lc.company_id
INNER JOIN landfill_mgmt.landfill_locations ll ON ws.location_id = ll.location_id
LEFT JOIN core_app.users u ON ws.created_by = u.user_id;

COMMENT ON VIEW landfill_mgmt.v_user_accessible_weigh_slips IS 'Complete view of weigh slips with all related information. Filter by user_construction_sites for access control.';


-- ============================================================================
-- GRANT PERMISSIONS (Adjust as needed)
-- ============================================================================

-- Example: Grant to application role
-- CREATE ROLE landfill_app_role;
-- GRANT USAGE ON SCHEMA core_app TO landfill_app_role;
-- GRANT USAGE ON SCHEMA landfill_mgmt TO landfill_app_role;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA core_app TO landfill_app_role;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA landfill_mgmt TO landfill_app_role;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA core_app TO landfill_app_role;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA landfill_mgmt TO landfill_app_role;


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Show all tables created
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname IN ('core_app', 'landfill_mgmt')
ORDER BY schemaname, tablename;