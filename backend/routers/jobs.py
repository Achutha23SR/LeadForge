import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import ScrapingJobCreate, ScrapingJobOut


router = APIRouter(prefix="/scraping/jobs", tags=["scraping"])
tasks: dict[str, asyncio.Task] = {}


def job_out(doc: dict) -> ScrapingJobOut:
    return ScrapingJobOut(**{key: doc.get(key) for key in ScrapingJobOut.model_fields})


async def process_job(job_id: str) -> None:
    await db.scraping_jobs.update_one({"id": job_id}, {"$set": {"status": "RUNNING", "started_at": datetime.now(timezone.utc)}})
    for page in range(1, 6):
        await asyncio.sleep(0.35)
        await db.scraping_jobs.update_one(
            {"id": job_id, "status": "RUNNING"},
            {"$set": {"pages_processed": page, "progress": page * 20, "records_discovered": page * 9, "records_enriched": max(0, page * 7), "records_failed": page if page > 3 else 0}},
        )
    await db.scraping_jobs.update_one({"id": job_id, "status": "RUNNING"}, {"$set": {"status": "COMPLETED", "progress": 100, "completed_at": datetime.now(timezone.utc)}})


@router.get("", response_model=list[ScrapingJobOut])
async def get_jobs(user: dict = Depends(get_current_user)):
    docs = await db.scraping_jobs.find({"owner_id": user["id"]}).sort("created_at", -1).to_list(100)
    return [job_out(doc) for doc in docs]


@router.post("", response_model=ScrapingJobOut)
async def create_job(payload: ScrapingJobCreate, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    doc = {
        "id": str(uuid.uuid4()), "owner_id": user["id"], "name": payload.name.strip(), "source": payload.source,
        "status": "QUEUED", "total_pages": 5, "pages_processed": 0, "records_discovered": 0,
        "records_enriched": 0, "records_failed": 0, "progress": 0, "country": payload.country,
        "industry": payload.industry, "job_title": payload.job_title, "created_at": now,
        "started_at": None, "completed_at": None,
    }
    await db.scraping_jobs.insert_one(doc)
    tasks[doc["id"]] = asyncio.create_task(process_job(doc["id"]))
    return job_out(doc)


@router.get("/{job_id}", response_model=ScrapingJobOut)
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    doc = await db.scraping_jobs.find_one({"id": job_id, "owner_id": user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    return job_out(doc)


@router.post("/{job_id}/cancel", response_model=ScrapingJobOut)
async def cancel_job(job_id: str, user: dict = Depends(get_current_user)):
    doc = await db.scraping_jobs.find_one_and_update({"id": job_id, "owner_id": user["id"], "status": {"$in": ["QUEUED", "RUNNING"]}}, {"$set": {"status": "CANCELLED"}}, return_document=ReturnDocument.AFTER)
    if not doc:
        raise HTTPException(status_code=409, detail="This job cannot be cancelled")
    task = tasks.get(job_id)
    if task:
        task.cancel()
    return job_out(doc)