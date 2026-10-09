def test_credits_and_analytics_have_breakdowns(auth_client):
    credits = auth_client.get('/credits')
    assert credits.status_code == 200, credits.text
    assert credits.json()['credits'] >= 0 and isinstance(credits.json()['transactions'], list)
    analytics = auth_client.get('/analytics')
    assert analytics.status_code == 200, analytics.text
    body = analytics.json()
    assert body['total_leads'] > 0
    assert body['leads_over_time'] and body['by_country'] and body['by_industry']
