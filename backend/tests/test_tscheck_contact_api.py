"""Backend coverage: authenticated Contact Us submission saved to MongoDB."""
import uuid


def test_contact_submission_saved(auth_client):
    payload = {
        "name": f"tscheck-contact-{uuid.uuid4().hex[:6]}",
        "email": "tscheck-contact@example.com",
        "message": "tscheck-contact-api automated backend test message content.",
    }
    resp = auth_client.post("/support/contact", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "RECEIVED"
    assert "id" in body
