"""Backend coverage: persons discovery and selection (search/filter/pagination/fields)."""


def test_persons_search_filter_pagination_fields(auth_client):
    resp = auth_client.get("/persons", params={"search": "", "industry": "all", "country": "all", "seniority": "all", "page": 1, "page_size": 5})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] > 0
    person = body["items"][0]
    for field in ["first_name", "last_name", "email", "job_title", "company_name", "industry", "city", "country"]:
        assert field in person, f"missing field {field}"

    # Filter by company name search term derived from the first result (deterministic, no seeded mutation)
    term = person["last_name"]
    filtered = auth_client.get("/persons", params={"search": term, "industry": "all", "country": "all", "seniority": "all", "page": 1, "page_size": 10})
    assert filtered.status_code == 200, filtered.text
    assert any(term.lower() in f"{item['first_name']} {item['last_name']}".lower() for item in filtered.json()["items"])

    # Pagination: page 2 with page_size 1 returns a different (or empty) item than page 1
    page1 = auth_client.get("/persons", params={"page": 1, "page_size": 1})
    page2 = auth_client.get("/persons", params={"page": 2, "page_size": 1})
    assert page1.status_code == 200 and page2.status_code == 200
    if page2.json()["items"]:
        assert page1.json()["items"][0]["id"] != page2.json()["items"][0]["id"]

    # Single person fetch
    detail = auth_client.get(f"/persons/{person['id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["email"] == person["email"]
