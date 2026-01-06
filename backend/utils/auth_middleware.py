from functools import wraps
from flask import request
from services.auth_service import AuthService
from utils.response import error_response


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return error_response('Authorization header required', 401)
        
        token = auth_header.split(' ')[1]
        user = AuthService.get_current_user(token)
        
        if not user:
            return error_response('Invalid or expired token', 401)
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """Helper to get current user from request context"""
    if hasattr(request, 'current_user'):
        return request.current_user
    
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        return AuthService.get_current_user(token)
    
    return None


def get_current_user_optional():
    """
    Get current user if authenticated, otherwise return None.
    Does not raise error for unauthenticated requests.
    """
    try:
        return get_current_user()
    except Exception:
        return None
