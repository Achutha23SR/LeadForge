def login(client):
    response = client.post("/auth/login", json={"email": "demo@leadforge.ai", "password": "demo1234"})
    assert response.status_code == 200


def test_company_search_and_pagination(client):
    login(client)
    response = client.get("/companies", params={"industry": "SaaS", "page": 1, "page_size": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert all(item["industry"] == "SaaS" for item in body["items"])


def test_person_search_and_email_validation(client):
    login(client)
    response = client.get("/persons", params={"page": 1, "page_size": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    assert "company_name" in body["items"][0]


def test_import_rejects_non_csv(client):
    login(client)
    response = client.post("/imports/preview", data={"entity_type": "companies"}, files={"file": ("bad.txt", b"hello", "text/plain")})
    assert response.status_code == 422