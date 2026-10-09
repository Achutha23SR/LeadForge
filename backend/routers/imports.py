import csv
import io
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import ImportCommitResponse, ImportPreview, ImportPreviewRow


router = APIRouter(prefix="/imports", tags=["imports"])


def clean(value: str | None) -> str:
    return (value or "").strip()


def domain_of(value: str) -> str:
    return re.sub(r"^https?://|^www\.", "", clean(value).lower()).split("/")[0]


@router.post("/preview", response_model=ImportPreview)
async def preview_import(
    entity_type: str = Form(...), file: UploadFile = File(...), user: dict = Depends(get_current_user),
):
    if entity_type not in ("companies", "persons"):
        raise HTTPException(status_code=422, detail="Import type must be companies or persons")
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Please upload a CSV file")
    raw = await file.read()
    if len(raw) > 2_000_000:
        raise HTTPException(status_code=413, detail="CSV files must be smaller than 2 MB")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="CSV must use UTF-8 encoding") from exc
    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise HTTPException(status_code=422, detail="CSV is missing a header row")
    rows: list[dict] = []
    seen: set[str] = set()
    for row_number, original in enumerate(reader, start=2):
        data = {clean(key).lower().replace(" ", "_"): clean(value) for key, value in original.items() if key}
        errors: list[str] = []
        duplicate = False
        if entity_type == "companies":
            data["domain"] = domain_of(data.get("domain") or data.get("website", ""))
            if not data.get("name"): errors.append("Company name is required")
            if not data.get("domain"): errors.append("Domain or website is required")
            key = data.get("domain", "")
            duplicate = bool(key and (key in seen or await db.companies.find_one({"domain": key})))
        else:
            data["email"] = data.get("email", "").lower()
            data["company_domain"] = domain_of(data.get("company_domain", ""))
            if not data.get("first_name"): errors.append("First name is required")
            if not data.get("last_name"): errors.append("Last name is required")
            if not data.get("email") or "@" not in data["email"]: errors.append("A valid email is required")
            if not data.get("company_domain"): errors.append("Company domain is required")
            elif not await db.companies.find_one({"domain": data["company_domain"]}): errors.append("Company domain does not exist")
            key = data.get("email", "")
            duplicate = bool(key and (key in seen or await db.contacts.find_one({"email": key})))
        if key: seen.add(key)
        rows.append({"row_number": row_number, "data": data, "valid": not errors and not duplicate, "duplicate": duplicate, "errors": errors})
        if len(rows) >= 500: break
    preview_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    doc = {"id": preview_id, "owner_id": user["id"], "entity_type": entity_type, "filename": file.filename or "import.csv", "rows": rows, "created_at": now}
    await db.imports.insert_one(doc)
    return ImportPreview(
        id=preview_id, entity_type=entity_type, filename=doc["filename"],
        rows=[ImportPreviewRow(**row) for row in rows], total_rows=len(rows),
        valid_rows=sum(1 for row in rows if row["valid"]), duplicate_rows=sum(1 for row in rows if row["duplicate"]),
        invalid_rows=sum(1 for row in rows if not row["valid"] and not row["duplicate"]),
    )


@router.post("/{preview_id}/commit", response_model=ImportCommitResponse)
async def commit_import(preview_id: str, user: dict = Depends(get_current_user)):
    preview = await db.imports.find_one({"id": preview_id, "owner_id": user["id"]})
    if not preview: raise HTTPException(status_code=404, detail="Import preview not found")
    if preview.get("committed_at"): raise HTTPException(status_code=409, detail="This preview was already imported")
    imported = 0
    now = datetime.now(timezone.utc)
    for row in preview["rows"]:
        if not row["valid"]: continue
        data = row["data"]
        if preview["entity_type"] == "companies":
            if await db.companies.find_one({"domain": data["domain"]}): continue
            company = {
                "id": str(uuid.uuid4()), "name": data["name"], "domain": data["domain"],
                "website": data.get("website") or f"https://{data['domain']}", "industry": data.get("industry") or "Other",
                "business_type": data.get("business_type") or "B2B", "employees": int(data.get("employees") or 0),
                "revenue": data.get("revenue") or "Not disclosed", "country": data.get("country") or "Unknown",
                "city": data.get("city") or "Unknown", "email": data.get("email") or f"hello@{data['domain']}",
                "linkedin_url": data.get("linkedin_url") or "", "founded_year": int(data.get("founded_year") or now.year),
                "technologies": [item.strip() for item in data.get("technologies", "").split(";") if item.strip()],
                "description": data.get("description") or "Imported company record.", "latitude": None, "longitude": None,
                "favorite": False, "created_at": now,
            }
            await db.companies.insert_one(company)
        else:
            if await db.contacts.find_one({"email": data["email"]}): continue
            company = await db.companies.find_one({"domain": data["company_domain"]})
            if not company: continue
            contact_id = str(uuid.uuid4())
            contact = {
                "id": contact_id, "first_name": data["first_name"], "last_name": data["last_name"],
                "email": data["email"], "job_title": data.get("job_title") or "Team Member",
                "department": data.get("department") or "Other", "seniority": data.get("seniority") or "Individual Contributor",
                "location": data.get("location") or f"{company['city']}, {company['country']}",
                "phone": data.get("phone") or None, "linkedin_url": data.get("linkedin_url") or None, "created_at": now,
            }
            await db.contacts.insert_one(contact)
            await db.leads.insert_one({
                "id": str(uuid.uuid4()), "company_id": company["id"], "contact_id": contact_id,
                "contact": contact, "company": company, "email_status": "UNKNOWN", "enriched": False,
                "score": 70, "created_at": now, "activity": [{"label": "Imported", "date": now.isoformat()}],
            })
        imported += 1
    await db.imports.update_one({"id": preview_id}, {"$set": {"committed_at": now, "imported": imported}})
    duplicates = sum(1 for row in preview["rows"] if row["duplicate"])
    invalid = sum(1 for row in preview["rows"] if not row["valid"] and not row["duplicate"])
    return ImportCommitResponse(imported=imported, skipped_duplicates=duplicates, skipped_invalid=invalid, message=f"Imported {imported} valid {preview['entity_type']} records")