from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from utils.response import success_response, error_response
from email_validator import validate_email, EmailNotValidError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')
    
    if not email or not password:
        return error_response('Email and password are required', 400)
    
    try:
        validate_email(email)
    except EmailNotValidError as e:
        return error_response(f'Invalid email: {str(e)}', 400)
    
    if len(password) < 6:
        return error_response('Password must be at least 6 characters', 400)
    
    try:
        user, token = AuthService.register(email, password, username)
        
        return success_response({
            'user': user.to_dict(),
            'access_token': token,
            'token_type': 'Bearer'
        }, message='Registration successful', status_code=201)
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f'Registration failed: {str(e)}', 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return error_response('Email and password are required', 400)
    
    try:
        user, token = AuthService.login(email, password)
        
        return success_response({
            'user': user.to_dict(),
            'access_token': token,
            'token_type': 'Bearer'
        }, message='Login successful')
    
    except ValueError as e:
        return error_response(str(e), 401)
    except Exception as e:
        return error_response(f'Login failed: {str(e)}', 500)


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response('Authorization header required', 401)
    
    token = auth_header.split(' ')[1]
    
    try:
        user = AuthService.get_current_user(token)
        
        if not user:
            return error_response('Invalid or expired token', 401)
        
        return success_response({
            'user': user.to_dict(include_sensitive=True)
        })
    
    except Exception as e:
        return error_response(f'Failed to get user: {str(e)}', 500)


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response('Authorization header required', 401)
    
    token = auth_header.split(' ')[1]
    data = request.get_json()
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return error_response('Old password and new password are required', 400)
    
    if len(new_password) < 6:
        return error_response('New password must be at least 6 characters', 400)
    
    try:
        user = AuthService.get_current_user(token)
        
        if not user:
            return error_response('Invalid or expired token', 401)
        
        AuthService.change_password(user, old_password, new_password)
        
        return success_response(message='Password changed successfully')
    
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f'Failed to change password: {str(e)}', 500)
