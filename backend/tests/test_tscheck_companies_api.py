"""Backend coverage: company data-management workflow (search/sort/favorite/edit)."""


def test_companies_search_filter_sort_favorite_edit(auth_client):
    # Search + filter + sort + pagination
    resp = auth_client.get("/companies", params={"search": "", "industry": "all", "country": "all", "sort_by": "employees", "sort_order": "desc", "page": 1, "page_size": 5})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body and "total" in body and body["total"] > 0
    company = body["items"][0]
    for field in ["name", "industry", "business_type", "employees", "revenue", "country", "city", "website", "email"]:
        assert field in company, f"missing field {field}"
    company_id = company["id"]

    # Toggle favorite
    fav_resp = auth_client.patch(f"/companies/{company_id}/favorite")
    assert fav_resp.status_code == 200, fav_resp.text
    toggled = fav_resp.json()["favorite"]
    # toggle back to restore seeded state (isolation discipline for seeded row)
    fav_resp2 = auth_client.patch(f"/companies/{company_id}/favorite")
    assert fav_resp2.status_code == 200
    assert fav_resp2.json()["favorite"] != toggled

    # Favorites filter works
    fav_resp3 = auth_client.patch(f"/companies/{company_id}/favorite")
    assert fav_resp3.json()["favorite"] is True
    fav_list = auth_client.get("/companies", params={"search": "", "industry": "all", "country": "all", "favorite": "true", "page": 1, "page_size": 20})
    assert fav_list.status_code == 200
    assert any(item["id"] == company_id for item in fav_list.json()["items"])
    auth_client.patch(f"/companies/{company_id}/favorite")  # revert

    # Edit: use an own-created-ish scoped update on seeded record, then revert
    detail = auth_client.get(f"/companies/{company_id}")
    assert detail.status_code == 200, detail.text
    original = detail.json()["company"]
    update_payload = {k: original[k] for k in ["name", "industry", "business_type", "employees", "revenue", "country", "city", "website", "email", "linkedin_url", "description"]}
    update_payload["description"] = "tscheck-companies-api edit check " + update_payload.get("description", "")[:50]
    put_resp = auth_client.put(f"/companies/{company_id}", json=update_payload)
    assert put_resp.status_code == 200, put_resp.text
    assert put_resp.json()["description"].startswith("tscheck-companies-api edit check")
    # revert description
    update_payload["description"] = original.get("description", "")
    revert = auth_client.put(f"/companies/{company_id}", json=update_payload)
    assert revert.status_code == 200
