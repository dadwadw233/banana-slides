"""
Order Model - Commercial Version
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, ForeignKey, JSON, Text
from models import db


class Order(db.Model):
    """订单模型"""
    __tablename__ = 'orders'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 订单详情
    order_number = db.Column(String(50), unique=True, nullable=False, index=True)  # e.g., "ORD20260105001"
    amount = db.Column(Numeric(10, 2), nullable=False)  # 总金额（CNY）
    quota_amount = db.Column(Integer, nullable=False)  # 购买的配额数量
    
    # 状态
    status = db.Column(String(20), default='pending', nullable=False, index=True)  # 'pending', 'paid', 'failed', 'refunded', 'cancelled'
    
    # 支付
    payment_method = db.Column(String(50), nullable=True)  # 'alipay', 'wechat', 'stripe', 'paypal'
    payment_id = db.Column(Text, nullable=True)  # 外部支付ID
    payment_data = db.Column(JSON, nullable=True)  # 支付提供商响应数据
    
    # 订阅（如果适用）
    subscription_type = db.Column(String(20), nullable=True)  # 'monthly', 'yearly', null for one-time
    subscription_id = db.Column(Integer, ForeignKey('subscriptions.id'), nullable=True)
    
    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    paid_at = db.Column(DateTime, nullable=True)
    refunded_at = db.Column(DateTime, nullable=True)
    
    # 关系
    quota_transactions = db.relationship('QuotaTransaction', backref='order', lazy=True)
    
    @staticmethod
    def generate_order_number():
        """生成订单号"""
        from datetime import datetime
        return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_number': self.order_number,
            'amount': float(self.amount) if self.amount else 0,
            'quota_amount': self.quota_amount,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_id': self.payment_id,
            'subscription_type': self.subscription_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
        }
    
    def __repr__(self):
        return f'<Order {self.order_number} status={self.status}>'
