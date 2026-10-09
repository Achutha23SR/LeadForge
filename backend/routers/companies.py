from fastapi import APIRouter, Depends, HTTPException

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import CompanyBrief, LeadOut
from routers.leads import lead_out


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyBrief])
async def get_companies(user: dict = Depends(get_current_user)):
    docs = await db.companies.find({}).sort("employees", -1).limit(100).to_list(100)
    return [CompanyBrief(**doc) for doc in docs]


@router.get("/{company_id}")
async def get_company(company_id: str, user: dict = Depends(get_current_user)):
    company = await db.companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    leads = await db.leads.find({"company_id": company_id}).to_list(100)
    return {"company": CompanyBrief(**company), "contacts": [lead_out(lead) for lead in leads]}