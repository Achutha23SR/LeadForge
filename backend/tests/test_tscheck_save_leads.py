from tests.conftest import search_one

def test_selected_lead_can_be_saved_to_new_list(auth_client):
    lead = search_one(auth_client)
    created = auth_client.post('/lists', json={'name':'tscheck-save-selected'})
    assert created.status_code == 200, created.text
    list_id = created.json()['id']
    response = auth_client.post(f'/lists/{list_id}/leads', json={'lead_ids':[lead['id']]})
    assert response.status_code == 200, response.text
    assert response.json()['added'] == 1
    detail = auth_client.get(f'/lists/{list_id}')
    assert detail.status_code == 200 and detail.json()['lead_count'] == 1
