from datetime import datetime
from pydantic import BaseModel, Field


class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "USER"
    credits: int = 1000


class AuthRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)


class AuthResponse(BaseModel):
    user: UserPublic | None = None
    message: str


class CompanyBrief(BaseModel):
    id: str
    name: str
    domain: str
    website: str
    industry: str
    country: str
    city: str
    employees: int
    revenue: str
    founded_year: int
    technologies: list[str] = []
    description: str = ""
    business_type: str = "B2B Software"
    email: str = ""
    linkedin_url: str = ""
    latitude: float | None = None
    longitude: float | None = None
    favorite: bool = False


class ContactBrief(BaseModel):
    id: str
    first_name: str
    last_name: str
    job_title: str
    department: str
    seniority: str
    location: str
    email: str
    phone: str | None = None
    linkedin_url: str | None = None


class CompanyUpdate(BaseModel):
    name: str = Field(min_length=2)
    industry: str = Field(min_length=2)
    business_type: str = Field(min_length=2)
    employees: int = Field(ge=0)
    revenue: str
    country: str
    city: str
    website: str
    email: str
    linkedin_url: str
    description: str = ""


class CompanyListResponse(BaseModel):
    items: list[CompanyBrief]
    total: int
    page: int
    page_size: int


class PersonOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    job_title: str
    department: str
    seniority: str
    location: str
    linkedin_url: str | None = None
    company_id: str
    company_name: str
    company_domain: str
    industry: str
    country: str
    city: str


class PersonListResponse(BaseModel):
    items: list[PersonOut]
    total: int
    page: int
    page_size: int


class ImportPreviewRow(BaseModel):
    row_number: int
    data: dict[str, str]
    valid: bool
    duplicate: bool
    errors: list[str] = []


class ImportPreview(BaseModel):
    id: str
    entity_type: str
    filename: str
    rows: list[ImportPreviewRow]
    total_rows: int
    valid_rows: int
    duplicate_rows: int
    invalid_rows: int


class ImportCommitResponse(BaseModel):
    imported: int
    skipped_duplicates: int
    skipped_invalid: int
    message: str


class EmailGenerateRequest(BaseModel):
    person_id: str
    tone: str
    objective: str
    context: str = Field(default="", max_length=1500)


class EmailDraftCreate(BaseModel):
    person_id: str
    tone: str
    objective: str
    subject: str = Field(min_length=2, max_length=200)
    body: str = Field(min_length=10, max_length=10000)


class EmailDraftOut(EmailDraftCreate):
    id: str
    created_at: datetime


class ContactSubmission(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=200)
    message: str = Field(min_length=10, max_length=3000)


class LeadOut(BaseModel):
    id: str
    company_id: str
    contact_id: str
    contact: ContactBrief
    company: CompanyBrief
    email_status: str
    enriched: bool = False
    created_at: datetime
    score: int = 80
    activity: list[dict] = []


class SearchFilters(BaseModel):
    query: str = ""
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    job_title: str | None = None
    seniority: str | None = None
    email_status: str | None = None
    min_employees: int | None = None
    max_employees: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)


class LeadSearchResponse(BaseModel):
    items: list[LeadOut]
    total: int
    page: int
    page_size: int
    credits_remaining: int


class LeadActionResponse(BaseModel):
    lead: LeadOut
    credits_remaining: int
    message: str


class ListCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class ListSummary(BaseModel):
    id: str
    name: str
    lead_count: int
    created_at: datetime
    updated_at: datetime


class ListDetail(ListSummary):
    leads: list[LeadOut] = []


class ScrapingJobCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    source: str = "Demo provider"
    country: str = "United States"
    industry: str = "SaaS"
    job_title: str = "CTO"


class ScrapingJobOut(BaseModel):
    id: str
    name: str
    source: str
    status: str
    total_pages: int
    pages_processed: int
    records_discovered: int
    records_enriched: int
    records_failed: int
    progress: int
    country: str
    industry: str
    job_title: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ExportCreate(BaseModel):
    lead_ids: list[str] = Field(min_length=1)


class ExportOut(BaseModel):
    id: str
    record_count: int
    status: str
    filename: str
    csv_content: str
    created_at: datetime
    credits_remaining: int


class DashboardMetric(BaseModel):
    label: str
    value: int
    delta: str
    tone: str = "blue"


class DashboardResponse(BaseModel):
    metrics: list[DashboardMetric]
    leads_over_time: list[dict]
    industry_breakdown: list[dict]
    recent_jobs: list[ScrapingJobOut]
    credits: int
    credit_used: int


class AnalyticsResponse(BaseModel):
    total_leads: int
    verified_emails: int
    enrichment_rate: int
    validation_rate: int
    credits_consumed: int
    leads_over_time: list[dict]
    by_country: list[dict]
    by_industry: list[dict]
    by_seniority: list[dict]