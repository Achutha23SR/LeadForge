def test_combined_lead_search_returns_paged_rows(auth_client):
    response = auth_client.post('/leads/search', json={'query':'','industry':'SaaS','country':'United States','job_title':'','email_status':'all','page':1,'page_size':5})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['page'] == 1 and body['page_size'] == 5
    assert body['total'] >= len(body['items'])
    assert len(body['items']) > 0

def test_search_requires_auth(client):
    response = client.post('/leads/search', json={'page':1,'page_size':5})
    assert response.status_code in (401, 403)
