"""
Quota Service - Commercial Version

提供配额消耗、充值、查询等服务
"""
from typing import Optional, List
from datetime import datetime
from models import db
from models.user import User
from models.quota_transaction import QuotaTransaction
from models.order import Order


class QuotaService:
    """配额管理服务"""
    
    # 配额消耗规则（每次操作消耗的配额数）
    QUOTA_COSTS = {
        'generate_outline': 0,  # 生成大纲免费
        'generate_description': 0.1,  # 生成单页描述
        'generate_image': 1,  # 生成单页图片
        'edit_image': 0.5,  # 编辑图片
        'export_pptx': 0.2,  # 导出PPTX
        'export_editable_pptx': 0.5,  # 导出可编辑PPTX
    }
    
    @staticmethod
    def get_balance(user: User) -> int:
        """获取用户配额余额"""
        return user.quota_balance
    
    @staticmethod
    def check_sufficient(user: User, action: str, count: int = 1) -> bool:
        """
        检查配额是否足够
        
        Args:
            user: 用户对象
            action: 操作类型
            count: 数量（如批量生成图片）
        
        Returns:
            bool: 是否足够
        """
        cost_per_item = QuotaService.QUOTA_COSTS.get(action, 1)
        total_cost = int(cost_per_item * count)
        return user.quota_balance >= total_cost
    
    @staticmethod
    def consume(user: User, action: str, count: int = 1, 
                project_id: Optional[int] = None, description: Optional[str] = None,
                extra_data: Optional[dict] = None) -> QuotaTransaction:
        """
        消耗配额
        
        Args:
            user: 用户对象
            action: 操作类型
            count: 数量
            project_id: 项目ID（可选）
            description: 描述（可选）
            extra_data: 额外数据（可选）
        
        Returns:
            QuotaTransaction对象
        
        Raises:
            ValueError: 配额不足
        """
        cost_per_item = QuotaService.QUOTA_COSTS.get(action, 1)
        total_cost = int(cost_per_item * count)
        
        if user.quota_balance < total_cost:
            raise ValueError(f'Insufficient quota. Required: {total_cost}, Available: {user.quota_balance}')
        
        # 扣除配额
        user.quota_balance -= total_cost
        
        # 记录交易
        transaction = QuotaTransaction(
            user_id=user.id,
            amount=-total_cost,
            balance_after=user.quota_balance,
            type='consume',
            project_id=project_id,
            description=description or f'{action} x {count}',
            extra_data=extra_data or {'action': action, 'count': count}
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def refund(transaction_id: int, reason: Optional[str] = None) -> QuotaTransaction:
        """
        退款配额（撤销之前的消耗）
        
        Args:
            transaction_id: 要退款的交易ID
            reason: 退款原因
        
        Returns:
            新的QuotaTransaction对象（退款记录）
        
        Raises:
            ValueError: 交易不存在或不能退款
        """
        original_transaction = QuotaTransaction.query.get(transaction_id)
        if not original_transaction:
            raise ValueError('Transaction not found')
        
        if original_transaction.type != 'consume':
            raise ValueError('Only consume transactions can be refunded')
        
        if original_transaction.amount >= 0:
            raise ValueError('Transaction amount must be negative for refund')
        
        # 获取用户
        user = User.query.get(original_transaction.user_id)
        if not user:
            raise ValueError('User not found')
        
        # 返还配额（原amount是负数，所以用abs）
        refund_amount = abs(original_transaction.amount)
        user.quota_balance += refund_amount
        
        # 记录退款交易
        refund_transaction = QuotaTransaction(
            user_id=user.id,
            amount=refund_amount,
            balance_after=user.quota_balance,
            type='refund',
            project_id=original_transaction.project_id,
            description=reason or f'Refund for transaction #{transaction_id}',
            extra_data={'original_transaction_id': transaction_id}
        )
        
        db.session.add(refund_transaction)
        db.session.commit()
        
        return refund_transaction
    
    @staticmethod
    def add_quota(user: User, amount: int, reason: str, order_id: Optional[int] = None) -> QuotaTransaction:
        """
        增加配额（购买、赠送等）
        
        Args:
            user: 用户对象
            amount: 增加数量
            reason: 原因
            order_id: 订单ID（如果是购买）
        
        Returns:
            QuotaTransaction对象
        """
        user.quota_balance += amount
        
        transaction_type = 'purchase' if order_id else 'gift'
        
        transaction = QuotaTransaction(
            user_id=user.id,
            amount=amount,
            balance_after=user.quota_balance,
            type=transaction_type,
            order_id=order_id,
            description=reason
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def get_transactions(user: User, page: int = 1, per_page: int = 20) -> tuple[List[QuotaTransaction], int]:
        """
        获取配额交易历史
        
        Args:
            user: 用户对象
            page: 页码
            per_page: 每页数量
        
        Returns:
            (交易列表, 总数)
        """
        query = QuotaTransaction.query.filter_by(user_id=user.id).order_by(QuotaTransaction.created_at.desc())
        total = query.count()
        transactions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return transactions, total
