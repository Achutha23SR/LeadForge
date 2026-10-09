"""Shared Mongo handle — import `client`/`db` from here (server.py, routers, seed.py)."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

load_dotenv(Path(__file__).parent.parent / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

logger = logging.getLogger(__name__)

# One entry per collection: every field a route filters, sorts, or dedupes on. Applied by ensure_indexes() at startup.
INDEXES: dict[str, list[IndexModel]] = {
    "status_checks": [IndexModel([("timestamp", DESCENDING)], name="timestamp_desc")],
    "users": [IndexModel([("email", ASCENDING)], name="email_unique", unique=True)],
    "companies": [
        IndexModel([("id", ASCENDING)], name="company_id", unique=True),
        IndexModel([("domain", ASCENDING)], name="company_domain", unique=True),
        IndexModel([("industry", ASCENDING), ("country", ASCENDING)], name="company_filters"),
    ],
    "contacts": [IndexModel([("id", ASCENDING)], name="contact_id", unique=True), IndexModel([("email", ASCENDING)], name="contact_email")],
    "leads": [
        IndexModel([("id", ASCENDING)], name="lead_id", unique=True),
        IndexModel([("company_id", ASCENDING)], name="lead_company"),
        IndexModel([("email_status", ASCENDING)], name="lead_email_status"),
    ],
    "lists": [IndexModel([("owner_id", ASCENDING), ("updated_at", DESCENDING)], name="list_owner_updated")],
    "scraping_jobs": [IndexModel([("owner_id", ASCENDING), ("created_at", DESCENDING)], name="job_owner_created"), IndexModel([("status", ASCENDING)], name="job_status")],
    "exports": [IndexModel([("owner_id", ASCENDING), ("created_at", DESCENDING)], name="export_owner_created")],
    "credit_transactions": [IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="credit_user_created")],
}


async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:  # one at a time so a bad spec skips only itself
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:  # never block boot on an index; the log line names what to fix
                logger.error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)
