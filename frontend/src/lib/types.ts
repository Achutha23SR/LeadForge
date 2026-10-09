export interface User { id: string; email: string; full_name: string; role: string; credits: number }
export interface AuthResponse { user: User | null; message: string }
export interface Company { id: string; name: string; domain: string; website: string; industry: string; country: string; city: string; employees: number; revenue: string; founded_year: number; technologies: string[]; description: string; business_type: string; email: string; linkedin_url: string; latitude?: number | null; longitude?: number | null; favorite: boolean }
export interface Contact { id: string; first_name: string; last_name: string; job_title: string; department: string; seniority: string; location: string; email: string; phone?: string | null; linkedin_url?: string | null }
export interface Lead { id: string; company_id: string; contact_id: string; contact: Contact; company: Company; email_status: string; enriched: boolean; created_at: string; score: number; activity: { label: string; date: string }[] }
export interface SearchFilters { query: string; industry?: string; country?: string; city?: string; job_title?: string; seniority?: string; email_status?: string; min_employees?: number; max_employees?: number; page: number; page_size: number }
export interface LeadSearchResponse { items: Lead[]; total: number; page: number; page_size: number; credits_remaining: number }
export interface LeadActionResponse { lead: Lead; credits_remaining: number; message: string }
export interface LeadList { id: string; name: string; lead_count: number; created_at: string; updated_at: string }
export interface ListDetail extends LeadList { leads: Lead[] }
export interface ScrapingJob { id: string; name: string; source: string; status: string; total_pages: number; pages_processed: number; records_discovered: number; records_enriched: number; records_failed: number; progress: number; country: string; industry: string; job_title: string; created_at: string; started_at?: string | null; completed_at?: string | null }
export interface ExportRecord { id: string; record_count: number; status: string; filename: string; csv_content: string; created_at: string; credits_remaining: number }
export interface Metric { label: string; value: number; delta: string; tone: string }
export interface DashboardData { metrics: Metric[]; leads_over_time: { date: string; leads: number; verified: number }[]; industry_breakdown: { name: string; value: number }[]; recent_jobs: ScrapingJob[]; credits: number; credit_used: number }
export interface AnalyticsData { total_leads: number; verified_emails: number; enrichment_rate: number; validation_rate: number; credits_consumed: number; leads_over_time: { date: string; leads: number; verified: number }[]; by_country: { name: string; value: number }[]; by_industry: { name: string; value: number }[]; by_seniority: { name: string; value: number }[] }
export interface CreditData { credits: number; credit_used: number; transactions: { id: string; type: string; amount: number; description: string; created_at: string }[] }
export interface CompanyListResponse { items: Company[]; total: number; page: number; page_size: number }
export interface Person { id: string; first_name: string; last_name: string; email: string; job_title: string; department: string; seniority: string; location: string; linkedin_url?: string | null; company_id: string; company_name: string; company_domain: string; industry: string; country: string; city: string }
export interface PersonListResponse { items: Person[]; total: number; page: number; page_size: number }
export interface ImportPreviewRow { row_number: number; data: Record<string, string>; valid: boolean; duplicate: boolean; errors: string[] }
export interface ImportPreview { id: string; entity_type: "companies" | "persons"; filename: string; rows: ImportPreviewRow[]; total_rows: number; valid_rows: number; duplicate_rows: number; invalid_rows: number }
export interface ImportSummary { imported: number; skipped_duplicates: number; skipped_invalid: number; message: string }
export interface GeneratedEmail { subject: string; body: string }
export interface EmailDraft extends GeneratedEmail { id: string; person_id: string; tone: string; objective: string; created_at: string }