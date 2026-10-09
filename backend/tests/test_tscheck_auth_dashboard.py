def test_login_reaches_dashboard(auth_client):
    dashboard = auth_client.get('/dashboard')
    assert dashboard.status_code == 200, dashboard.text
    body = dashboard.json()
    assert len(body['metrics']) >= 4
    assert body['credits'] >= 0

def test_invalid_login_rejected(client):
    response = client.post('/auth/login', json={'email':'demo@leadforge.ai','password':'wrong-password'})
    assert response.status_code == 401
