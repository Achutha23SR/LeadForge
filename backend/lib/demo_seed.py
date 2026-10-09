import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from lib.auth import hash_password
from lib.db import db


COMPANIES = [
    ("Northstar Labs", "northstarlabs.io", "SaaS", "United States", "Austin", 120, "$10M–$25M", ["React", "AWS", "HubSpot"]),
    ("SignalNest", "signalnest.com", "Marketing Tech", "United States", "New York", 85, "$5M–$10M", ["Segment", "Snowflake", "Stripe"]),
    ("Lattice Peak", "latticepeak.co", "Fintech", "United Kingdom", "London", 240, "$25M–$50M", ["Python", "GCP", "Plaid"]),
    ("Orbit Harbor", "orbitharbor.com", "SaaS", "Canada", "Toronto", 64, "$5M–$10M", ["Vue", "AWS", "Intercom"]),
    ("CinderStack", "cinderstack.dev", "Developer Tools", "United States", "San Francisco", 310, "$50M–$100M", ["Kubernetes", "Go", "Datadog"]),
    ("Morrow Health", "morrowhealth.com", "Health Tech", "United States", "Boston", 180, "$25M–$50M", ["Next.js", "Azure", "Twilio"]),
    ("Vela Commerce", "velacommerce.io", "E-commerce", "Germany", "Berlin", 95, "$10M–$25M", ["Shopify", "Klaviyo", "AWS"]),
    ("Brightline Ops", "brightlineops.com", "SaaS", "Australia", "Sydney", 52, "$1M–$5M", ["Ruby", "Heroku", "Zendesk"]),
    ("Aster Grid", "astergrid.ai", "AI & Data", "United States", "Seattle", 430, "$100M+", ["Python", "Snowflake", "OpenAI"]),
    ("Clearpath Legal", "clearpathlegal.com", "Legal Tech", "United States", "Chicago", 72, "$5M–$10M", ["Django", "AWS", "DocuSign"]),
    ("Juniper Works", "juniperworks.co", "SaaS", "France", "Paris", 145, "$10M–$25M", ["Node.js", "GCP", "Notion"]),
    ("Tandem Fleet", "tandemfleet.com", "Logistics", "United States", "Denver", 260, "$25M–$50M", ["React", "Postgres", "Mapbox"]),
]

PEOPLE = [
    ("Maya", "Chen", "Chief Technology Officer", "Engineering", "C-Level"),
    ("Ethan", "Brooks", "VP of Sales", "Sales", "VP"),
    ("Priya", "Nair", "Head of Marketing", "Marketing", "Director"),
    ("Lucas", "Martin", "Director of Engineering", "Engineering", "Director"),
    ("Sofia", "Rossi", "Chief Revenue Officer", "Sales", "C-Level"),
    ("Noah", "Williams", "Product Manager", "Product", "Manager"),
]


async def seed_demo_data() -> None:
    now = datetime.now(timezone.utc)
    demo = await db.users.find_one({"email": "demo@leadforge.ai"})
    if not demo:
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "demo@leadforge.ai", "full_name": "Alex Morgan",
            "password_hash": hash_password("demo1234"), "role": "USER", "credits": 1000,
            "credit_used": 0, "disabled": False, "created_at": now,
        })
    admin = await db.users.find_one({"email": "admin@leadforge.ai"})
    if not admin:
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": "admin@leadforge.ai", "full_name": "LeadForge Admin",
            "password_hash": hash_password("admin1234"), "role": "ADMIN", "credits": 5000,
            "credit_used": 0, "disabled": False, "created_at": now,
        })

    if await db.companies.count_documents({}) > 0:
        return

    company_docs: list[dict] = []
    contact_docs: list[dict] = []
    lead_docs: list[dict] = []
    for index, company in enumerate(COMPANIES):
        name, domain, industry, country, city, employees, revenue, technologies = company
        company_id = str(uuid.uuid4())
        company_doc = {
            "id": company_id, "name": name, "domain": domain, "website": f"https://{domain}",
            "industry": industry, "country": country, "city": city, "employees": employees,
            "revenue": revenue, "founded_year": 2014 + index % 8, "technologies": technologies,
            "description": f"{name} builds modern software for ambitious operating teams.", "created_at": now,
        }
        company_docs.append(company_doc)
        for person_index, person in enumerate(PEOPLE[:3] if index % 2 == 0 else PEOPLE[3:]):
            first, last, title, department, seniority = person
            contact_id = str(uuid.uuid4())
            email = f"{first.lower()}.{last.lower()}@{domain}"
            contact_doc = {
                "id": contact_id, "first_name": first, "last_name": last, "job_title": title,
                "department": department, "seniority": seniority, "location": f"{city}, {country}",
                "email": email, "phone": f"+1 (555) 01{index:02d}-{person_index + 10:04d}",
                "linkedin_url": f"https://linkedin.com/in/{first.lower()}-{last.lower()}",
                "created_at": now - timedelta(days=(index + person_index) * 2),
            }
            contact_docs.append(contact_doc)
            status = "VERIFIED" if (index + person_index) % 3 != 1 else "RISKY"
            lead_docs.append({
                "id": str(uuid.uuid4()), "company_id": company_id, "contact_id": contact_id,
                "company": company_doc, "contact": contact_doc, "email_status": status,
                "enriched": (index + person_index) % 4 != 0, "score": 72 + ((index * 7 + person_index * 5) % 25),
                "created_at": now - timedelta(days=(index % 9)),
                "activity": [{"label": "Created", "date": (now - timedelta(days=index % 9)).isoformat()}],
            })
    await db.companies.insert_many(company_docs)
    await db.contacts.insert_many(contact_docs)
    await db.leads.insert_many(lead_docs)

    user = await db.users.find_one({"email": "demo@leadforge.ai"})
    if user:
        await db.lists.insert_one({
            "id": str(uuid.uuid4()), "owner_id": user["id"], "name": "US SaaS Targets",
            "lead_ids": [lead["id"] for lead in lead_docs[:6]], "created_at": now - timedelta(days=4), "updated_at": now,
        })
        await db.lists.insert_one({
            "id": str(uuid.uuid4()), "owner_id": user["id"], "name": "Priority Decision Makers",
            "lead_ids": [lead["id"] for lead in lead_docs[6:10]], "created_at": now - timedelta(days=2), "updated_at": now,
        })


async def main() -> None:
    await seed_demo_data()


if __name__ == "__main__":
    asyncio.run(main())