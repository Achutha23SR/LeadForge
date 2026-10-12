from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import AnalyticsResponse, DashboardMetric, DashboardResponse
from routers.jobs import job_out

router = APIRouter(tags=["dashboard"])


def _last_7_days_series(leads: list[dict]) -> list[dict]:
    """Return a list of 7 dicts with date + leads + verified counts for the last 7 days."""
    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=6 - i)) for i in range(7)]
    day_leads: dict = {d: 0 for d in days}
    day_verified: dict = {d: 0 for d in days}
    for lead in leads:
        created = lead.get("created_at")
        if isinstance(created, datetime):
            d = created.date()
            if d in day_leads:
                day_leads[d] += 1
                if lead.get("email_status") == "VERIFIED":
                    day_verified[d] += 1
    return [{"date": d.strftime("%b %-d"), "leads": day_leads[d], "verified": day_verified[d]} for d in days]


async def lead_docs():
    return await db.leads.find({}).to_list(1000)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(user: dict = Depends(get_current_user)):
    leads = await lead_docs()
    verified = sum(1 for lead in leads if lead.get("email_status") == "VERIFIED")
    enriched = sum(1 for lead in leads if lead.get("enriched"))
    jobs = await db.scraping_jobs.find({"owner_id": user["id"]}).sort("created_at", -1).limit(4).to_list(4)
    industry_counts: dict[str, int] = {}
    for lead in leads:
        industry = lead["company"]["industry"]
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
    user_doc = await db.users.find_one({"id": user["id"]})
    metrics = [
        DashboardMetric(label="Total leads", value=len(leads), delta="+18.4%", tone="blue"),
        DashboardMetric(label="Verified emails", value=verified, delta="+12.2%", tone="green"),
        DashboardMetric(label="Companies", value=await db.companies.count_documents({}), delta="+8.1%", tone="cyan"),
        DashboardMetric(label="Credits used", value=int(user_doc.get("credit_used", 0)), delta="This cycle", tone="amber"),
    ]
    return DashboardResponse(
        metrics=metrics,
        leads_over_time=_last_7_days_series(leads),
        industry_breakdown=[{"name": key, "value": value} for key, value in sorted(industry_counts.items(), key=lambda item: item[1], reverse=True)[:6]],
        recent_jobs=[job_out(job) for job in jobs], credits=int(user_doc.get("credits", 0)), credit_used=int(user_doc.get("credit_used", 0)),
    )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(user: dict = Depends(get_current_user)):
    leads = await lead_docs()
    verified = sum(1 for lead in leads if lead.get("email_status") == "VERIFIED")
    enriched = sum(1 for lead in leads if lead.get("enriched"))
    by_country: dict[str, int] = {}
    by_industry: dict[str, int] = {}
    by_seniority: dict[str, int] = {}
    for lead in leads:
        by_country[lead["company"]["country"]] = by_country.get(lead["company"]["country"], 0) + 1
        by_industry[lead["company"]["industry"]] = by_industry.get(lead["company"]["industry"], 0) + 1
        by_seniority[lead["contact"]["seniority"]] = by_seniority.get(lead["contact"]["seniority"], 0) + 1
    user_doc = await db.users.find_one({"id": user["id"]})
    return AnalyticsResponse(
        total_leads=len(leads), verified_emails=verified, enrichment_rate=round(enriched / len(leads) * 100) if leads else 0,
        validation_rate=round(verified / len(leads) * 100) if leads else 0, credits_consumed=int(user_doc.get("credit_used", 0)),
        leads_over_time=_last_7_days_series(leads),
        by_country=[{"name": key, "value": value} for key, value in by_country.items()],
        by_industry=[{"name": key, "value": value} for key, value in by_industry.items()],
        by_seniority=[{"name": key, "value": value} for key, value in by_seniority.items()],
    )


@router.get("/credits")
async def get_credits(user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"id": user["id"]})
    transactions = await db.credit_transactions.find({"user_id": user["id"]}).sort("created_at", -1).limit(25).to_list(25)
    return {"credits": int(user_doc.get("credits", 0)), "credit_used": int(user_doc.get("credit_used", 0)), "transactions": [{"id": item["id"], "type": item["type"], "amount": item["amount"], "description": item["description"], "created_at": item["created_at"]} for item in transactions]}
