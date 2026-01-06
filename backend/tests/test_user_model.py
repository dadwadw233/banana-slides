import pytest
from models.user import User


def test_create_user(db_session):
    user = User(
        email='newuser@example.com',
        username='newuser',
        quota_balance=5
    )
    user.set_password('password123')
    
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.email == 'newuser@example.com'
    assert user.quota_balance == 5
    assert user.role == 'user'
    assert user.status == 'active'


def test_password_hashing(db_session):
    user = User(email='test@test.com')
    user.set_password('mypassword')
    
    assert user.password_hash is not None
    assert user.password_hash != 'mypassword'
    assert user.check_password('mypassword') is True
    assert user.check_password('wrongpassword') is False


def test_user_to_dict(sample_user):
    user_dict = sample_user.to_dict()
    
    assert user_dict['email'] == 'test@example.com'
    assert user_dict['username'] == 'testuser'
    assert user_dict['quota_balance'] == 10
    assert 'password_hash' not in user_dict


def test_user_to_dict_with_sensitive(sample_user):
    user_dict = sample_user.to_dict(include_sensitive=True)
    
    assert 'phone' in user_dict
    assert 'oauth_provider' in user_dict
    assert 'last_login_at' in user_dict
