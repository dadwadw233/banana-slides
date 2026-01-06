from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from services.quota_service import QuotaService
from utils.response import success_response, error_response

quota_bp = Blueprint('quota', __name__, url_prefix='/api/quota')


@quota_bp.route('/balance', methods=['GET'])
def get_balance():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response('Authorization header required', 401)
    
    token = auth_header.split(' ')[1]
    
    try:
        user = AuthService.get_current_user(token)
        
        if not user:
            return error_response('Invalid or expired token', 401)
        
        balance = QuotaService.get_balance(user)
        
        return success_response({
            'balance': balance,
            'user_id': user.id
        })
    
    except Exception as e:
        return error_response(f'Failed to get balance: {str(e)}', 500)


@quota_bp.route('/transactions', methods=['GET'])
def get_transactions():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response('Authorization header required', 401)
    
    token = auth_header.split(' ')[1]
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if per_page > 100:
        per_page = 100
    
    try:
        user = AuthService.get_current_user(token)
        
        if not user:
            return error_response('Invalid or expired token', 401)
        
        transactions, total = QuotaService.get_transactions(user, page, per_page)
        
        return success_response({
            'transactions': [t.to_dict() for t in transactions],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        return error_response(f'Failed to get transactions: {str(e)}', 500)


@quota_bp.route('/check', methods=['POST'])
def check_quota():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response('Authorization header required', 401)
    
    token = auth_header.split(' ')[1]
    data = request.get_json()
    
    action = data.get('action')
    count = data.get('count', 1)
    
    if not action:
        return error_response('Action is required', 400)
    
    try:
        user = AuthService.get_current_user(token)
        
        if not user:
            return error_response('Invalid or expired token', 401)
        
        is_sufficient = QuotaService.check_sufficient(user, action, count)
        cost = QuotaService.QUOTA_COSTS.get(action, 1) * count
        
        return success_response({
            'sufficient': is_sufficient,
            'current_balance': user.quota_balance,
            'required': int(cost),
            'action': action,
            'count': count
        })
    
    except Exception as e:
        return error_response(f'Failed to check quota: {str(e)}', 500)
