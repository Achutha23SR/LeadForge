"""Live HTTP fixtures for LeadForge endpoint checks."""
import os
import httpx
import pytest
import pytest_asyncio

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API_URL = f"{BACKEND_URL}/api"

def api_url(path: str = "") -> str:
    return f"{API_URL}{path}"

@pytest.fixture(scope="session")
def backend_url():
    return BACKEND_URL

@pytest.fixture
def client():
    with httpx.Client(base_url=API_URL, timeout=30.0) as c:
        yield c

@pytest_asyncio.fixture
async def aclient():
    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as c:
        yield c

@pytest.fixture
def auth_client(client):
    response = client.post("/auth/login", json={"email":"demo@leadforge.ai","password":"demo1234"})
    assert response.status_code == 200, response.text
    return client

def search_one(client):
    response = client.post("/leads/search", json={"query":"","industry":"all","country":"all","job_title":"","email_status":"all","page":1,"page_size":1})
    assert response.status_code == 200, response.text
    return response.json()["items"][0]
