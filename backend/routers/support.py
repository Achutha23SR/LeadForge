import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import ContactSubmission


router = APIRouter(prefix="/support", tags=["support"])


@router.post("/contact")
async def contact_support(payload: ContactSubmission, user: dict = Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), "owner_id": user["id"], **payload.model_dump(), "status": "RECEIVED", "created_at": datetime.now(timezone.utc)}
    await db.contact_submissions.insert_one(doc)
    return {"id": doc["id"], "status": "RECEIVED", "message": "Your message has been received"}