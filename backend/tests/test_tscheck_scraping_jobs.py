import time

def test_demo_scraping_job_completes(auth_client):
    created = auth_client.post('/scraping/jobs', json={'name':'tscheck-demo-job','source':'Demo provider','country':'United States','industry':'SaaS','job_title':'CTO'})
    assert created.status_code == 200, created.text
    job_id = created.json()['id']
    assert created.json()['status'] == 'QUEUED'
    deadline = time.time() + 8
    body = created.json()
    while time.time() < deadline:
        response = auth_client.get(f'/scraping/jobs/{job_id}')
        assert response.status_code == 200, response.text
        body = response.json()
        if body['status'] == 'COMPLETED': break
        time.sleep(0.4)
    assert body['status'] == 'COMPLETED'
    assert body['progress'] == 100 and body['records_discovered'] > 0 and body['records_enriched'] > 0
