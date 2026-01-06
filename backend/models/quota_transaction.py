"""
Quota Transaction Model - Commercial Version
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, JSON
from models import db


class QuotaTransaction(db.Model):
    """配额交易记录模型"""
    __tablename__ = 'quota_transactions'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 交易详情
    amount = db.Column(Integer, nullable=False)  # 正数为充值/赠送，负数为消耗
    balance_after = db.Column(Integer, nullable=False)  # 交易后余额
    type = db.Column(String(20), nullable=False, index=True)  # 'purchase', 'consume', 'refund', 'gift', 'expire'
    
    # 关联实体
    order_id = db.Column(Integer, ForeignKey('orders.id'), nullable=True)
    project_id = db.Column(Integer, ForeignKey('projects.id'), nullable=True)
    
    # 描述
    description = db.Column(Text, nullable=True)
    extra_data = db.Column(JSON, nullable=True)  # 附加数据，如 {"action": "generate_image", "page_id": 123}
    
    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'balance_after': self.balance_after,
            'type': self.type,
            'order_id': self.order_id,
            'project_id': self.project_id,
            'description': self.description,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<QuotaTransaction user={self.user_id} amount={self.amount} type={self.type}>'
