import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import ListCreate, ListDetail, ListSummary
from routers.leads import lead_out


router = APIRouter(prefix="/lists", tags=["lists"])


def summary(doc: dict) -> ListSummary:
    return ListSummary(id=doc["id"], name=doc["name"], lead_count=len(doc.get("lead_ids", [])), created_at=doc["created_at"], updated_at=doc["updated_at"])


@router.get("", response_model=list[ListSummary])
async def get_lists(user: dict = Depends(get_current_user)):
    docs = await db.lists.find({"owner_id": user["id"]}).sort("updated_at", -1).to_list(100)
    return [summary(doc) for doc in docs]


@router.post("", response_model=ListSummary)
async def create_list(payload: ListCreate, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    doc = {"id": str(uuid.uuid4()), "owner_id": user["id"], "name": payload.name.strip(), "lead_ids": [], "created_at": now, "updated_at": now}
    await db.lists.insert_one(doc)
    return summary(doc)


@router.get("/{list_id}", response_model=ListDetail)
async def get_list(list_id: str, user: dict = Depends(get_current_user)):
    doc = await db.lists.find_one({"id": list_id, "owner_id": user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")
    leads = await db.leads.find({"id": {"$in": doc.get("lead_ids", [])}}).to_list(100)
    lead_map = {lead["id"]: lead for lead in leads}
    return ListDetail(**summary(doc).model_dump(), leads=[lead_out(lead_map[lid]) for lid in doc.get("lead_ids", []) if lid in lead_map])


@router.post("/{list_id}/leads")
async def add_to_list(list_id: str, payload: dict[str, list[str]], user: dict = Depends(get_current_user)):
    ids = payload.get("lead_ids", [])
    doc = await db.lists.find_one({"id": list_id, "owner_id": user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")
    valid = await db.leads.count_documents({"id": {"$in": ids}})
    existing = doc.get("lead_ids", [])
    new_ids = [lead_id for lead_id in ids[:valid] if lead_id not in existing]
    now = datetime.now(timezone.utc)
    await db.lists.update_one({"id": list_id}, {"$addToSet": {"lead_ids": {"$each": new_ids}}, "$set": {"updated_at": now}})
    return {"added": len(new_ids), "message": f"Added {len(new_ids)} lead(s) to {doc['name']}"}


@router.delete("/{list_id}/leads/{lead_id}")
async def remove_from_list(list_id: str, lead_id: str, user: dict = Depends(get_current_user)):
    result = await db.lists.update_one({"id": list_id, "owner_id": user["id"]}, {"$pull": {"lead_ids": lead_id}, "$set": {"updated_at": datetime.now(timezone.utc)}})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="List not found")
    return {"message": "Lead removed"}


@router.delete("/{list_id}")
async def delete_list(list_id: str, user: dict = Depends(get_current_user)):
    result = await db.lists.delete_one({"id": list_id, "owner_id": user["id"]})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="List not found")
    return {"message": "List deleted"}