from tests.conftest import search_one

def test_create_list_add_and_inspect_member(auth_client):
    name = 'tscheck-list-membership'
    created = auth_client.post('/lists', json={'name':name})
    assert created.status_code == 200, created.text
    list_id = created.json()['id']
    lead = search_one(auth_client)
    added = auth_client.post(f'/lists/{list_id}/leads', json={'lead_ids':[lead['id']]})
    assert added.status_code == 200, added.text
    assert added.json()['added'] == 1
    detail = auth_client.get(f'/lists/{list_id}')
    assert detail.status_code == 200, detail.text
    assert detail.json()['name'] == name and any(item['id'] == lead['id'] for item in detail.json()['leads'])
