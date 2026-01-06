import pytest
from services.auth_service import AuthService
from models.user import User


def test_register_new_user(app, db_session):
    with app.app_context():
        user, token = AuthService.register(
            email='newuser@example.com',
            password='password123',
            username='newuser'
        )
        
        assert user.id is not None
        assert user.email == 'newuser@example.com'
        assert user.username == 'newuser'
        assert user.quota_balance == 3
        assert token is not None
        assert len(token) > 20


def test_register_duplicate_email(app, db_session, sample_user):
    with app.app_context():
        with pytest.raises(ValueError, match='Email already exists'):
            AuthService.register(
                email='test@example.com',
                password='password123'
            )


def test_login_success(app, db_session, sample_user):
    with app.app_context():
        user, token = AuthService.login(
            email='test@example.com',
            password='test123456'
        )
        
        assert user.id == sample_user.id
        assert token is not None


def test_login_wrong_password(app, db_session, sample_user):
    with app.app_context():
        with pytest.raises(ValueError, match='Invalid email or password'):
            AuthService.login(
                email='test@example.com',
                password='wrongpassword'
            )


def test_login_nonexistent_user(app, db_session):
    with app.app_context():
        with pytest.raises(ValueError, match='Invalid email or password'):
            AuthService.login(
                email='nonexistent@example.com',
                password='password123'
            )


def test_verify_token(app, db_session, sample_user):
    with app.app_context():
        _, token = AuthService.login('test@example.com', 'test123456')
        
        payload = AuthService.verify_token(token)
        assert payload is not None
        assert payload['user_id'] == sample_user.id


def test_verify_invalid_token(app):
    with app.app_context():
        payload = AuthService.verify_token('invalid.token.here')
        assert payload is None


def test_get_current_user(app, db_session, sample_user):
    with app.app_context():
        _, token = AuthService.login('test@example.com', 'test123456')
        
        user = AuthService.get_current_user(token)
        assert user is not None
        assert user.id == sample_user.id


def test_change_password(app, db_session, sample_user):
    with app.app_context():
        result = AuthService.change_password(
            sample_user,
            'test123456',
            'newpassword123'
        )
        
        assert result is True
        assert sample_user.check_password('newpassword123')
        assert not sample_user.check_password('test123456')


def test_change_password_wrong_old(app, db_session, sample_user):
    with app.app_context():
        with pytest.raises(ValueError, match='Old password is incorrect'):
            AuthService.change_password(
                sample_user,
                'wrongoldpassword',
                'newpassword123'
            )
