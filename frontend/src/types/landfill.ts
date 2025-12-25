// Landfill Workflow Types

export interface ConstructionSite {
  site_id: number;
  site_name: string;
  site_code: string;
  address?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: number;
  assigned_users_count?: number;
  weigh_slips_count?: number;
}

export interface Company {
  company_id: number;
  company_name: string;
  company_code?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
}

export interface Location {
  location_id: number;
  location_name: string;
  company_id: number;
  company_name?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
}

export interface MaterialType {
  material_id: number;
  material_code: string;
  material_name: string;
  onorm_code?: string;
  is_hazardous: boolean;
  is_active: boolean;
  created_at: string;
}

export interface PdfDocument {
  document_id: number;
  file_name: string;
  file_path: string;
  file_size: number;
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  total_pages?: number;
  extracted_slips_count?: number;
  error_message?: string;
  created_at: string;
  processed_at?: string;
  created_by: number;
}

export interface WeighSlip {
  slip_id: number;
  document_id?: number;
  slip_number: string;
  delivery_date: string;
  site_id?: number;
  site_name?: string;
  material_id?: number;
  material_name?: string;
  material_code?: string;
  company_id?: number;
  company_name?: string;
  location_id?: number;
  location_name?: string;
  net_weight_kg: number;
  gross_weight_kg?: number;
  tare_weight_kg?: number;
  is_hazardous: boolean;
  vehicle_license_plate?: string;
  transporter_name?: string;
  waste_origin_address?: string;
  invoice_number?: string;
  assignment_status: 'PENDING' | 'ASSIGNED';
  onorm_code?: string;
  created_at: string;
  updated_at: string;
  created_by: number;
}

export interface HazardousSlip {
  hazardous_slip_id: number;
  document_id?: number;
  weigh_slip_id?: number;
  begleitschein_number: string;
  waste_code: string;
  specification?: string;
  mass_kg: number;
  disposal_method?: string;
  transport_date: string;
  transporter_company?: string;
  receiver_company?: string;
  page_image_base64?: string;
  created_at: string;
  created_by: number;
}

export interface DataExport {
  export_id: number;
  export_type: 'EXCEL' | 'PDF';
  file_name: string;
  file_path: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  filters?: Record<string, unknown>;
  created_at: string;
  completed_at?: string;
  expires_at: string;
  created_by: number;
}

// Filter Types
export interface WeighSlipFilters {
  page?: number;
  page_size?: number;
  site_id?: number;
  material_id?: number;
  company_id?: number;
  location_id?: number;
  from_date?: string;
  to_date?: string;
  is_hazardous?: boolean;
  assignment_status?: 'PENDING' | 'ASSIGNED';
  search?: string;
}

export interface DocumentFilters {
  page?: number;
  page_size?: number;
  status?: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  from_date?: string;
  to_date?: string;
}
