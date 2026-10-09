from tests.conftest import search_one

def test_lead_detail_and_actions(auth_client):
    lead = search_one(auth_client)
    detail = auth_client.get(f"/leads/{lead['id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()['id'] == lead['id']
    enrich = auth_client.post(f"/leads/{lead['id']}/enrich")
    assert enrich.status_code == 200, enrich.text
    assert enrich.json()['lead']['enriched'] is True
    validate = auth_client.post(f"/leads/{lead['id']}/validate")
    assert validate.status_code == 200, validate.text
    assert validate.json()['lead']['email_status'] in ('VERIFIED','RISKY','INVALID')
