"""
Subscription Model - Commercial Version
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, Boolean, ForeignKey
from models import db


class Subscription(db.Model):
    """订阅模型"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 订阅详情
    type = db.Column(String(20), nullable=False)  # 'monthly', 'yearly'
    quota_per_period = db.Column(Integer, nullable=False)  # 每周期配额，如月度50次，年度800次
    price = db.Column(Numeric(10, 2), nullable=False)  # 价格
    
    # 状态
    status = db.Column(String(20), default='active', nullable=False, index=True)  # 'active', 'cancelled', 'expired'
    
    # 账单
    current_period_start = db.Column(DateTime, nullable=False)
    current_period_end = db.Column(DateTime, nullable=False)
    next_billing_date = db.Column(DateTime, nullable=True, index=True)
    
    # 自动续费
    auto_renew = db.Column(Boolean, default=True, nullable=False)
    
    # 外部ID（用于支付平台）
    stripe_subscription_id = db.Column(String(255), nullable=True)
    
    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at = db.Column(DateTime, nullable=True)
    expired_at = db.Column(DateTime, nullable=True)
    
    # 关系
    orders = db.relationship('Order', backref='subscription', lazy=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'quota_per_period': self.quota_per_period,
            'price': float(self.price) if self.price else 0,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
            'auto_renew': self.auto_renew,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Subscription user={self.user_id} type={self.type} status={self.status}>'
