from tests.conftest import search_one

def test_export_selected_lead_and_history(auth_client):
    lead = search_one(auth_client)
    response = auth_client.post('/exports', json={'lead_ids':[lead['id']]})
    assert response.status_code == 200, response.text
    export = response.json()
    assert export['status'] == 'COMPLETED' and export['record_count'] == 1
    assert 'First Name' in export['csv_content']
    history = auth_client.get('/exports')
    assert history.status_code == 200, history.text
    assert any(item['id'] == export['id'] for item in history.json())
