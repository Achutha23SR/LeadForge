import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ASCENDING, DESCENDING, ReturnDocument

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import CompanyBrief, CompanyListResponse, CompanyUpdate
from routers.leads import lead_out


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
async def get_companies(
    search: str = "", industry: str = "all", country: str = "all", favorite: bool | None = None,
    sort_by: str = Query(default="employees", pattern="^(name|industry|employees|revenue|country)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"), page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50), user: dict = Depends(get_current_user),
):
    conditions: list[dict[str, Any]] = []
    if search.strip():
        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        conditions.append({"$or": [{"name": pattern}, {"domain": pattern}, {"email": pattern}, {"city": pattern}]})
    if industry != "all": conditions.append({"industry": industry})
    if country != "all": conditions.append({"country": country})
    if favorite is not None: conditions.append({"favorite": favorite})
    query = {"$and": conditions} if conditions else {}
    total = await db.companies.count_documents(query)
    docs = await db.companies.find(query).sort(sort_by, ASCENDING if sort_order == "asc" else DESCENDING).skip((page - 1) * page_size).limit(page_size).to_list(page_size)
    return CompanyListResponse(items=[CompanyBrief(**doc) for doc in docs], total=total, page=page, page_size=page_size)


@router.get("/{company_id}")
async def get_company(company_id: str, user: dict = Depends(get_current_user)):
    company = await db.companies.find_one({"id": company_id})
    if not company: raise HTTPException(status_code=404, detail="Company not found")
    leads = await db.leads.find({"company_id": company_id}).to_list(100)
    return {"company": CompanyBrief(**company), "contacts": [lead_out(lead) for lead in leads]}


@router.put("/{company_id}", response_model=CompanyBrief)
async def update_company(company_id: str, payload: CompanyUpdate, user: dict = Depends(get_current_user)):
    values = payload.model_dump()
    doc = await db.companies.find_one_and_update({"id": company_id}, {"$set": values}, return_document=ReturnDocument.AFTER)
    if not doc: raise HTTPException(status_code=404, detail="Company not found")
    await db.leads.update_many({"company_id": company_id}, {"$set": {f"company.{key}": value for key, value in values.items()}})
    return CompanyBrief(**doc)


@router.patch("/{company_id}/favorite", response_model=CompanyBrief)
async def toggle_favorite(company_id: str, user: dict = Depends(get_current_user)):
    current = await db.companies.find_one({"id": company_id})
    if not current: raise HTTPException(status_code=404, detail="Company not found")
    value = not current.get("favorite", False)
    doc = await db.companies.find_one_and_update({"id": company_id}, {"$set": {"favorite": value}}, return_document=ReturnDocument.AFTER)
    await db.leads.update_many({"company_id": company_id}, {"$set": {"company.favorite": value}})
    return CompanyBrief(**doc)