import re
from typing import Any

from fastapi import APIRouter, Depends, Query
from pymongo import DESCENDING

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import PersonListResponse, PersonOut


router = APIRouter(prefix="/persons", tags=["persons"])


def person_out(lead: dict[str, Any]) -> PersonOut:
    contact, company = lead["contact"], lead["company"]
    return PersonOut(
        id=contact["id"], first_name=contact["first_name"], last_name=contact["last_name"],
        email=contact["email"], job_title=contact["job_title"], department=contact["department"],
        seniority=contact["seniority"], location=contact["location"], linkedin_url=contact.get("linkedin_url"),
        company_id=company["id"], company_name=company["name"], company_domain=company["domain"],
        industry=company["industry"], country=company["country"], city=company["city"],
    )


@router.get("", response_model=PersonListResponse)
async def get_persons(
    search: str = "", industry: str = "all", country: str = "all", seniority: str = "all",
    page: int = Query(default=1, ge=1), page_size: int = Query(default=10, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    conditions: list[dict[str, Any]] = []
    if search.strip():
        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        conditions.append({"$or": [{"contact.first_name": pattern}, {"contact.last_name": pattern}, {"contact.email": pattern}, {"contact.job_title": pattern}, {"company.name": pattern}]})
    if industry != "all": conditions.append({"company.industry": industry})
    if country != "all": conditions.append({"company.country": country})
    if seniority != "all": conditions.append({"contact.seniority": seniority})
    query = {"$and": conditions} if conditions else {}
    total = await db.leads.count_documents(query)
    docs = await db.leads.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size).to_list(page_size)
    return PersonListResponse(items=[person_out(doc) for doc in docs], total=total, page=page, page_size=page_size)


@router.get("/{person_id}", response_model=PersonOut)
async def get_person(person_id: str, user: dict = Depends(get_current_user)):
    lead = await db.leads.find_one({"contact_id": person_id})
    if not lead:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Person not found")
    return person_out(lead)