import csv
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import ExportCreate, ExportOut
from routers.leads import credit_user


router = APIRouter(prefix="/exports", tags=["exports"])


def csv_for(leads: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["First Name", "Last Name", "Job Title", "Company", "Industry", "Country", "City", "Email", "Email Status", "Phone", "LinkedIn", "Website", "Employees"])
    for lead in leads:
        contact, company = lead["contact"], lead["company"]
        writer.writerow([contact["first_name"], contact["last_name"], contact["job_title"], company["name"], company["industry"], company["country"], company["city"], contact["email"], lead.get("email_status", "UNKNOWN"), contact.get("phone", ""), contact.get("linkedin_url", ""), company["website"], company["employees"]])
    return output.getvalue()


@router.get("", response_model=list[ExportOut])
async def get_exports(user: dict = Depends(get_current_user)):
    docs = await db.exports.find({"owner_id": user["id"]}).sort("created_at", -1).to_list(50)
    current = await db.users.find_one({"id": user["id"]})
    return [ExportOut(**{**doc, "credits_remaining": int(current.get("credits", 0))}) for doc in docs]


@router.post("", response_model=ExportOut)
async def create_export(payload: ExportCreate, user: dict = Depends(get_current_user)):
    leads = await db.leads.find({"id": {"$in": payload.lead_ids}}).to_list(100)
    if not leads:
        raise HTTPException(status_code=404, detail="No valid leads selected")
    charge = max(1, (len(leads) + 99) // 100)
    current = await credit_user(user["id"], charge, "EXPORT")
    now = datetime.now(timezone.utc)
    content = csv_for(leads)
    doc = {"id": str(uuid.uuid4()), "owner_id": user["id"], "record_count": len(leads), "status": "COMPLETED", "filename": f"leadforge-export-{now.strftime('%Y%m%d-%H%M')}.csv", "csv_content": content, "created_at": now}
    await db.exports.insert_one(doc)
    return ExportOut(**{**doc, "credits_remaining": int(current.get("credits", 0))})


@router.get("/{export_id}", response_model=ExportOut)
async def get_export(export_id: str, user: dict = Depends(get_current_user)):
    doc = await db.exports.find_one({"id": export_id, "owner_id": user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Export not found")
    current = await db.users.find_one({"id": user["id"]})
    return ExportOut(**{**doc, "credits_remaining": int(current.get("credits", 0))})