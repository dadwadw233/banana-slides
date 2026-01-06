from typing import Optional
from datetime import datetime
from models import db
from models.user import User
from models.order import Order
from models.quota_transaction import QuotaTransaction
from services.quota_service import QuotaService


class OrderService:
    
    PRICING = {
        '10_pack': {'quota': 10, 'price': 18.00, 'name': '10次套餐'},
        '50_pack': {'quota': 50, 'price': 80.00, 'name': '50次套餐'},
        '100_pack': {'quota': 100, 'price': 150.00, 'name': '100次套餐'},
        '500_pack': {'quota': 500, 'price': 700.00, 'name': '500次套餐'},
    }
    
    @staticmethod
    def create_order(user: User, package_type: str) -> Order:
        if package_type not in OrderService.PRICING:
            raise ValueError(f'Invalid package type: {package_type}')
        
        package = OrderService.PRICING[package_type]
        
        order = Order(
            user_id=user.id,
            order_number=Order.generate_order_number(),
            amount=package['price'],
            quota_amount=package['quota'],
            status='pending',
            payment_method=None
        )
        
        db.session.add(order)
        db.session.commit()
        
        return order
    
    @staticmethod
    def process_payment(order_id: int, payment_method: str, payment_id: str) -> Order:
        order = Order.query.get(order_id)
        
        if not order:
            raise ValueError('Order not found')
        
        if order.status != 'pending':
            raise ValueError(f'Order status is {order.status}, cannot process payment')
        
        order.status = 'paid'
        order.payment_method = payment_method
        order.payment_id = payment_id
        order.paid_at = datetime.utcnow()
        
        user = User.query.get(order.user_id)
        if not user:
            raise ValueError('User not found')
        
        QuotaService.add_quota(
            user=user,
            amount=order.quota_amount,
            reason=f'Purchase {order.quota_amount} quota via order {order.order_number}',
            order_id=order.id
        )
        
        db.session.commit()
        
        return order
    
    @staticmethod
    def cancel_order(order_id: int, reason: Optional[str] = None) -> Order:
        order = Order.query.get(order_id)
        
        if not order:
            raise ValueError('Order not found')
        
        if order.status == 'cancelled':
            raise ValueError('Order already cancelled')
        
        if order.status == 'paid':
            raise ValueError('Paid order cannot be cancelled. Please request refund instead.')
        
        order.status = 'cancelled'
        
        db.session.commit()
        
        return order
    
    @staticmethod
    def get_user_orders(user: User, page: int = 1, per_page: int = 20):
        query = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc())
        total = query.count()
        orders = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return orders, total
