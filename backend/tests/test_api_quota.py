import pytest


def test_get_quota_balance(client, db_session, auth_headers):
    response = client.get('/api/quota/balance', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert 'balance' in data['data']
    assert data['data']['balance'] == 10


def test_get_quota_balance_no_auth(client, db_session):
    response = client.get('/api/quota/balance')
    
    assert response.status_code == 401


def test_get_quota_transactions(client, db_session, auth_headers, sample_user, app):
    with app.app_context():
        from services.quota_service import QuotaService
        QuotaService.consume(sample_user, 'generate_image', 1)
        QuotaService.add_quota(sample_user, 5, 'Test add')
    
    response = client.get('/api/quota/transactions?page=1&per_page=10', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert 'transactions' in data['data']
    assert 'pagination' in data['data']
    assert len(data['data']['transactions']) == 2


def test_check_quota_sufficient(client, db_session, auth_headers):
    response = client.post('/api/quota/check',
        headers=auth_headers,
        json={
            'action': 'generate_image',
            'count': 5
        }
    )
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert data['data']['sufficient'] is True
    assert data['data']['required'] == 5
    assert data['data']['current_balance'] == 10


def test_check_quota_insufficient(client, db_session, auth_headers):
    response = client.post('/api/quota/check',
        headers=auth_headers,
        json={
            'action': 'generate_image',
            'count': 20
        }
    )
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert data['data']['sufficient'] is False


def test_check_quota_no_action(client, db_session, auth_headers):
    response = client.post('/api/quota/check',
        headers=auth_headers,
        json={'count': 5}
    )
    
    assert response.status_code == 400
