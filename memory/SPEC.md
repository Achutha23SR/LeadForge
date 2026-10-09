# LeadForge MVP Spec

## Product
LeadForge is a dark-first B2B prospecting workspace for discovering demo company/contact records, filtering leads, saving lists, enriching and validating records, launching safe demo scraping jobs, and exporting CSV files.

## Data model
MongoDB collections: users, companies, contacts, leads, lists, scraping_jobs, exports, credit_transactions. Lead records denormalize company/contact data for fast filtered search. User-owned collections are scoped by owner_id.

## Key flows
- `/login` authenticates with an httpOnly `lf_session` cookie and redirects to the dashboard.
- Dashboard shows metrics, activity bars, industry mix, and recent scraping jobs.
- Lead search POSTs combined query/industry/country/title/status/employee filters, charges one credit, and supports selection, list save, enrichment, validation, detail drawer, pagination, and CSV export.
- Lists can be created, inspected, populated from lead search, and deleted.
- Scraping jobs are queued through the DemoLeadProvider and progress asynchronously in the backend task runner through QUEUED → RUNNING → COMPLETED.
- Credits and analytics are backed by API queries; exports store generated CSV content and can be downloaded again.

## Auth and roles
JWTs are stored only in the httpOnly `lf_session` cookie. USER and ADMIN roles are stored on the user. Admin accounts are seeded for role-aware extension, while the MVP UI uses the USER workspace.

## Provider boundary
All discovery, enrichment, and validation behavior is deterministic demo behavior. No prohibited websites, CAPTCHA bypasses, authentication bypasses, or anti-bot workarounds are used. The scraping job API is designed to swap in an allowed provider later.