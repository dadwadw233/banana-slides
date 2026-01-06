"""
User Model - Commercial Version
"""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from models import db
import bcrypt


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(Integer, primary_key=True)
    
    # 基本信息
    email = db.Column(String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(255), nullable=True)  # OAuth用户可能没有密码
    username = db.Column(String(100), nullable=True)
    full_name = db.Column(String(200), nullable=True)
    avatar_url = db.Column(Text, nullable=True)
    phone = db.Column(String(20), nullable=True)
    
    # 配额
    quota_balance = db.Column(Integer, default=0, nullable=False)
    
    # 角色与状态
    role = db.Column(String(20), default='user', nullable=False)  # 'user', 'premium', 'admin'
    status = db.Column(String(20), default='active', nullable=False)  # 'active', 'suspended', 'deleted'
    is_verified = db.Column(Boolean, default=False, nullable=False)
    is_email_verified = db.Column(Boolean, default=False, nullable=False)
    is_phone_verified = db.Column(Boolean, default=False, nullable=False)
    
    # OAuth
    oauth_provider = db.Column(String(50), nullable=True)  # 'google', 'wechat', 'github'
    oauth_id = db.Column(String(255), nullable=True)
    
    # 元数据
    last_login_at = db.Column(DateTime, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = db.Column(DateTime, nullable=True)
    
    # 关系
    projects = db.relationship('Project', backref='user', lazy=True)
    quota_transactions = db.relationship('QuotaTransaction', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def set_password(self, password: str):
        """设置密码（加密存储）"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'quota_balance': self.quota_balance,
            'role': self.role,
            'status': self.status,
            'is_verified': self.is_verified,
            'is_email_verified': self.is_email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                'phone': self.phone,
                'oauth_provider': self.oauth_provider,
                'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'
