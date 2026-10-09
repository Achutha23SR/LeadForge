# LeadForge MVP Spec

## Product
LeadForge is a dark-first B2B prospecting workspace for managing companies and persons, importing CSV data, discovering demo records, generating personalized outreach, saving lists, enriching and validating leads, launching safe demo scraping jobs, and exporting CSV files.

## Data model
MongoDB collections: users, companies, contacts, leads, lists, scraping_jobs, exports, credit_transactions, imports, email_drafts, contact_submissions. Lead records denormalize company/contact data for fast filtered search. User-owned collections are scoped by owner_id.

## Key flows
- `/login` authenticates with an httpOnly `lf_session` cookie and redirects to the dashboard.
- Dashboard shows metrics, activity bars, industry mix, and recent scraping jobs.
- Lead search POSTs combined query/industry/country/title/status/employee filters, charges one credit, and supports selection, list save, enrichment, validation, detail drawer, pagination, and CSV export.
- Lists can be created, inspected, populated from lead search, and deleted.
- Scraping jobs are queued through the DemoLeadProvider and progress asynchronously in the backend task runner through QUEUED → RUNNING → COMPLETED.
- Credits and analytics are backed by API queries; exports store generated CSV content and can be downloaded again.
- Companies supports server-side search/filter/sort/pagination, detail/edit, favorites, external website/LinkedIn links, and an OpenStreetMap/Leaflet coordinate view.
- Persons supports server-side search/filter/pagination, multi-selection, external LinkedIn links, and direct handoff to the email composer.
- CSV import validates UTF-8 company or person files, previews row errors and duplicates, and commits only valid non-duplicate rows. Companies dedupe by normalized domain; persons by lowercase email.
- The AI Email Generator streams OpenAI GPT-5.4 output through the FastAPI backend, supports tone/objective/context controls, editable subject/body, clipboard copy, MongoDB draft saving, and mail-client links.
- Documentation describes API and CSV schemas. Contact Us saves authenticated workspace submissions in MongoDB.

## Auth and roles
JWTs are stored only in the httpOnly `lf_session` cookie. USER and ADMIN roles are stored on the user. Admin accounts are seeded for role-aware extension, while the MVP UI uses the USER workspace.

## Provider boundary
Discovery, enrichment, and validation remain deterministic demo behavior. Email generation uses OpenAI GPT-5.4 through the Emergent Universal LLM key. No prohibited websites, CAPTCHA bypasses, authentication bypasses, automated LinkedIn messaging, or anti-bot workarounds are used. The scraping job API is designed to swap in an allowed provider later.