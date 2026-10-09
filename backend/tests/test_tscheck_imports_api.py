"""Backend coverage: CSV import preview (valid/duplicate/invalid) and commit."""
import io
import uuid


def test_companies_csv_import_preview_and_commit(auth_client):
    unique_domain = f"tscheck-import-{uuid.uuid4().hex[:8]}.com"
    csv_content = (
        "name,domain,industry,business_type,employees,revenue,country,city,email\n"
        f"TscheckImportCo,{unique_domain},SaaS,B2B,50,$1M,United States,Austin,hello@{unique_domain}\n"
        f"TscheckImportCo,{unique_domain},SaaS,B2B,50,$1M,United States,Austin,hello@{unique_domain}\n"  # duplicate within file
        ",,SaaS,B2B,10,$1M,United States,Austin,bad@bad.com\n"  # invalid: missing name/domain
    )
    files = {"file": ("tscheck-import.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"entity_type": "companies"}
    preview_resp = auth_client.post("/imports/preview", files=files, data=data)
    assert preview_resp.status_code == 200, preview_resp.text
    preview = preview_resp.json()
    assert preview["total_rows"] == 3
    assert preview["valid_rows"] == 1
    assert preview["duplicate_rows"] == 1
    assert preview["invalid_rows"] == 1

    commit_resp = auth_client.post(f"/imports/{preview['id']}/commit")
    assert commit_resp.status_code == 200, commit_resp.text
    summary = commit_resp.json()
    assert summary["imported"] == 1
    assert summary["skipped_duplicates"] >= 1
    assert summary["skipped_invalid"] >= 1

    # Verify it now appears in companies list
    lookup = auth_client.get("/companies", params={"search": unique_domain, "page": 1, "page_size": 5})
    assert lookup.status_code == 200
    assert any(item["domain"] == unique_domain for item in lookup.json()["items"])
