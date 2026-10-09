"""Backend coverage: AI Email Generator live OpenAI GPT-5.4 streaming generation + draft save."""
import json


def _first_person(auth_client):
    resp = auth_client.get("/persons", params={"page": 1, "page_size": 1})
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    assert items, "seed data must include at least one person"
    return items[0]


def test_email_generate_streams_and_draft_saves(auth_client):
    person = _first_person(auth_client)
    payload = {"person_id": person["id"], "tone": "Professional", "objective": "Introduction", "context": "tscheck automated test context"}
    with auth_client.stream("POST", "/email/generate", json=payload, timeout=60.0) as resp:
        assert resp.status_code == 200
        raw_text = "".join(resp.iter_text())

    final = None
    for block in raw_text.split("\n\n"):
        if not block.strip():
            continue
        event = next((line[6:].strip() for line in block.split("\n") if line.startswith("event:")), None)
        data_line = next((line for line in block.split("\n") if line.startswith("data:")), None)
        if not data_line:
            continue
        data = json.loads(data_line[5:].strip())
        if event == "result":
            final = data
        if event == "error":
            raise AssertionError(f"email generation stream errored: {data}")

    assert final is not None, f"no final subject/body payload found in stream (first 300 chars): {raw_text[:300]}"
    assert final.get("subject") and final.get("body")

    draft_payload = {"person_id": person["id"], "tone": "Professional", "objective": "Introduction", "subject": final["subject"], "body": final["body"]}
    draft_resp = auth_client.post("/email/drafts", json=draft_payload)
    assert draft_resp.status_code == 200, draft_resp.text
    draft = draft_resp.json()
    assert draft["subject"] == final["subject"]

    list_resp = auth_client.get("/email/drafts")
    assert list_resp.status_code == 200
    assert any(d["id"] == draft["id"] for d in list_resp.json())
