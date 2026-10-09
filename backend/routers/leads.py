import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import LeadActionResponse, LeadOut, LeadSearchResponse, SearchFilters


router = APIRouter(prefix="/leads", tags=["leads"])


def lead_out(doc: dict[str, Any]) -> LeadOut:
    return LeadOut(
        id=doc["id"], company_id=doc["company_id"], contact_id=doc["contact_id"],
        contact=doc["contact"], company=doc["company"], email_status=doc.get("email_status", "UNKNOWN"),
        enriched=doc.get("enriched", False), created_at=doc["created_at"], score=doc.get("score", 80),
        activity=doc.get("activity", []),
    )


async def credit_user(user_id: str, amount: int, operation: str) -> dict[str, Any]:
    updated = await db.users.find_one_and_update(
        {"id": user_id, "credits": {"$gte": amount}},
        {"$inc": {"credits": -amount, "credit_used": amount}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=402, detail="Not enough credits for this operation")
    await db.credit_transactions.insert_one({
        "id": str(uuid.uuid4()), "user_id": user_id, "type": operation, "amount": amount,
        "description": operation.title().replace("_", " "), "created_at": datetime.now(timezone.utc),
    })
    return updated


def build_filter(filters: SearchFilters) -> dict[str, Any]:
    conditions: list[dict[str, Any]] = []
    if filters.query.strip():
        pattern = {"$regex": re.escape(filters.query.strip()), "$options": "i"}
        conditions.append({"$or": [{"company.name": pattern}, {"company.domain": pattern}, {"contact.first_name": pattern}, {"contact.last_name": pattern}, {"contact.job_title": pattern}]})
    for key, value in (("company.industry", filters.industry), ("company.country", filters.country), ("company.city", filters.city), ("contact.job_title", filters.job_title), ("contact.seniority", filters.seniority), ("email_status", filters.email_status)):
        if value and value != "all":
            conditions.append({key: {"$regex": re.escape(value), "$options": "i"}})
    if filters.min_employees is not None:
        conditions.append({"company.employees": {"$gte": filters.min_employees}})
    if filters.max_employees is not None:
        conditions.append({"company.employees": {"$lte": filters.max_employees}})
    return {"$and": conditions} if conditions else {}


async def run_search(filters: SearchFilters, user_id: str, charge: bool = True) -> LeadSearchResponse:
    user = await credit_user(user_id, 1, "SEARCH") if charge else await db.users.find_one({"id": user_id})
    query = build_filter(filters)
    total = await db.leads.count_documents(query)
    docs = await db.leads.find(query).sort("score", -1).skip((filters.page - 1) * filters.page_size).limit(filters.page_size).to_list(filters.page_size)
    return LeadSearchResponse(items=[lead_out(doc) for doc in docs], total=total, page=filters.page, page_size=filters.page_size, credits_remaining=int(user.get("credits", 0)))


@router.post("/search", response_model=LeadSearchResponse)
async def search_leads(filters: SearchFilters, user: dict = Depends(get_current_user)):
    return await run_search(filters, user["id"])


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: str, user: dict = Depends(get_current_user)):
    doc = await db.leads.find_one({"id": lead_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead_out(doc)


@router.post("/{lead_id}/enrich", response_model=LeadActionResponse)
async def enrich_lead(lead_id: str, user: dict = Depends(get_current_user)):
    await credit_user(user["id"], 2, "ENRICHMENT")
    now = datetime.now(timezone.utc)
    doc = await db.leads.find_one_and_update(
        {"id": lead_id},
        {"$set": {"enriched": True}, "$push": {"activity": {"label": "Enriched", "date": now.isoformat()}}},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Lead not found")
    current = await db.users.find_one({"id": user["id"]})
    return LeadActionResponse(lead=lead_out(doc), credits_remaining=int(current.get("credits", 0)), message="Lead enriched with the demo provider")


@router.post("/{lead_id}/validate", response_model=LeadActionResponse)
async def validate_lead(lead_id: str, user: dict = Depends(get_current_user)):
    await credit_user(user["id"], 1, "VALIDATION")
    doc = await db.leads.find_one({"id": lead_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Lead not found")
    email = doc["contact"]["email"]
    status = "INVALID" if "invalid" in email or email.endswith(".example") else ("RISKY" if "test" in email else "VERIFIED")
    now = datetime.now(timezone.utc)
    doc = await db.leads.find_one_and_update(
        {"id": lead_id},
        {"$set": {"email_status": status}, "$push": {"activity": {"label": "Validated", "date": now.isoformat()}}},
        return_document=ReturnDocument.AFTER,
    )
    current = await db.users.find_one({"id": user["id"]})
    return LeadActionResponse(lead=lead_out(doc), credits_remaining=int(current.get("credits", 0)), message=f"Email marked {status.lower()}")


@router.post("/bulk-enrich")
async def bulk_enrich(payload: dict[str, list[str]], user: dict = Depends(get_current_user)):
    ids = payload.get("lead_ids", [])
    if not ids or len(ids) > 50:
        raise HTTPException(status_code=422, detail="Select between 1 and 50 leads")
    await credit_user(user["id"], 2 * len(ids), "ENRICHMENT")
    await db.leads.update_many({"id": {"$in": ids}}, {"$set": {"enriched": True}})
    current = await db.users.find_one({"id": user["id"]})
    return {"updated": len(ids), "credits_remaining": int(current.get("credits", 0)), "message": f"Enriched {len(ids)} leads"}


@router.post("/bulk-validate")
async def bulk_validate(payload: dict[str, list[str]], user: dict = Depends(get_current_user)):
    ids = payload.get("lead_ids", [])
    if not ids or len(ids) > 50:
        raise HTTPException(status_code=422, detail="Select between 1 and 50 leads")
    await credit_user(user["id"], len(ids), "VALIDATION")
    docs = await db.leads.find({"id": {"$in": ids}}).to_list(50)
    for doc in docs:
        email = doc["contact"]["email"]
        status = "INVALID" if "invalid" in email else "VERIFIED"
        await db.leads.update_one({"id": doc["id"]}, {"$set": {"email_status": status}})
    current = await db.users.find_one({"id": user["id"]})
    return {"updated": len(docs), "credits_remaining": int(current.get("credits", 0)), "message": f"Validated {len(docs)} leads"}