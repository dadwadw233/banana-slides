"""
Authentication Service - Commercial Version

提供用户注册、登录、JWT生成和验证等认证服务
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app
from models import db
from models.user import User


class AuthService:
    """认证服务"""
    
    @staticmethod
    def generate_token(user_id: int, expires_in_hours: int = 24) -> str:
        """生成JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow()
        }
        
        secret = current_app.config.get('SECRET_KEY', 'your-secret-key-change-this')
        token = jwt.encode(payload, secret, algorithm='HS256')
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证JWT token"""
        try:
            secret = current_app.config.get('SECRET_KEY', 'your-secret-key-change-this')
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token已过期
        except jwt.InvalidTokenError:
            return None  # Token无效
    
    @staticmethod
    def register(email: str, password: str, username: Optional[str] = None) -> tuple[User, str]:
        """
        注册新用户
        
        Args:
            email: 邮箱
            password: 密码
            username: 用户名（可选）
        
        Returns:
            (User对象, JWT token)
        
        Raises:
            ValueError: 邮箱已存在或参数无效
        """
        # 验证邮箱是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValueError('Email already exists')
        
        # 创建新用户
        user = User(
            email=email,
            username=username or email.split('@')[0],
            quota_balance=3,  # 新用户赠送3次免费配额
            role='user',
            status='active'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 生成token
        token = AuthService.generate_token(user.id)
        
        return user, token
    
    @staticmethod
    def login(email: str, password: str) -> tuple[User, str]:
        """
        用户登录
        
        Args:
            email: 邮箱
            password: 密码
        
        Returns:
            (User对象, JWT token)
        
        Raises:
            ValueError: 邮箱或密码错误
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            raise ValueError('Invalid email or password')
        
        if user.status != 'active':
            raise ValueError('User account is not active')
        
        if not user.check_password(password):
            raise ValueError('Invalid email or password')
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        # 生成token
        token = AuthService.generate_token(user.id)
        
        return user, token
    
    @staticmethod
    def get_current_user(token: str) -> Optional[User]:
        """
        从token获取当前用户
        
        Args:
            token: JWT token
        
        Returns:
            User对象或None
        """
        payload = AuthService.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        user = User.query.get(user_id)
        if not user or user.status != 'active':
            return None
        
        return user
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> bool:
        """
        修改密码
        
        Args:
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            bool: 是否成功
        
        Raises:
            ValueError: 旧密码错误
        """
        if not user.check_password(old_password):
            raise ValueError('Old password is incorrect')
        
        user.set_password(new_password)
        db.session.commit()
        
        return True
