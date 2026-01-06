import pytest


def test_register_success(client, db_session):
    response = client.post('/api/auth/register', json={
        'email': 'newuser@test.com',
        'password': 'password123',
        'username': 'newuser'
    })
    
    assert response.status_code == 201
    data = response.json
    assert data['success'] is True
    assert 'access_token' in data['data']
    assert data['data']['user']['email'] == 'newuser@test.com'
    assert data['data']['user']['quota_balance'] == 3


def test_register_invalid_email(client, db_session):
    response = client.post('/api/auth/register', json={
        'email': 'invalid-email',
        'password': 'password123'
    })
    
    assert response.status_code == 400


def test_register_duplicate_email(client, db_session, sample_user):
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 400


def test_login_success(client, db_session, sample_user):
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'test123456'
    })
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert 'access_token' in data['data']


def test_login_wrong_password(client, db_session, sample_user):
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401


def test_get_current_user(client, db_session, auth_headers):
    response = client.get('/api/auth/me', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert data['data']['user']['email'] == 'test@example.com'


def test_get_current_user_no_token(client, db_session):
    response = client.get('/api/auth/me')
    
    assert response.status_code == 401


def test_get_current_user_invalid_token(client, db_session):
    response = client.get('/api/auth/me', headers={
        'Authorization': 'Bearer invalid.token.here'
    })
    
    assert response.status_code == 401


def test_change_password(client, db_session, auth_headers):
    response = client.post('/api/auth/change-password', 
        headers=auth_headers,
        json={
            'old_password': 'test123456',
            'new_password': 'newpassword123'
        }
    )
    
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True


def test_change_password_wrong_old(client, db_session, auth_headers):
    response = client.post('/api/auth/change-password',
        headers=auth_headers,
        json={
            'old_password': 'wrongoldpassword',
            'new_password': 'newpassword123'
        }
    )
    
    assert response.status_code == 400
