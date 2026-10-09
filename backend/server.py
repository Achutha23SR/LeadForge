from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from lib.demo_seed import seed_demo_data
from routers import auth, companies, dashboard, exports, jobs, leads, lists


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
from lib.db import client, db, ensure_indexes


# Startup runs before the yield, shutdown after it. Add your own setup/teardown here.
@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    await seed_demo_data()
    yield
    client.close()


# Create the main app without a prefix
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "LeadForge API ready", "provider": "DemoLeadProvider"}

api_router.include_router(auth.router)
api_router.include_router(companies.router)
api_router.include_router(leads.router)
api_router.include_router(lists.router)
api_router.include_router(jobs.router)
api_router.include_router(exports.router)
api_router.include_router(dashboard.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Keep this as the final statement so every endpoint is mounted under /api.
app.include_router(api_router)
