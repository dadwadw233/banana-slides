import pytest
from services.order_service import OrderService
from models.order import Order


def test_create_order(app, db_session, sample_user):
    with app.app_context():
        order = OrderService.create_order(sample_user, '50_pack')
        
        assert order.id is not None
        assert order.user_id == sample_user.id
        assert order.amount == 80.00
        assert order.quota_amount == 50
        assert order.status == 'pending'
        assert order.order_number is not None


def test_create_order_invalid_package(app, db_session, sample_user):
    with app.app_context():
        with pytest.raises(ValueError, match='Invalid package type'):
            OrderService.create_order(sample_user, 'invalid_pack')


def test_process_payment(app, db_session, sample_user):
    with app.app_context():
        order = OrderService.create_order(sample_user, '10_pack')
        initial_quota = sample_user.quota_balance
        
        completed_order = OrderService.process_payment(
            order_id=order.id,
            payment_method='alipay',
            payment_id='TEST_PAY_123'
        )
        
        assert completed_order.status == 'paid'
        assert completed_order.payment_method == 'alipay'
        assert completed_order.payment_id == 'TEST_PAY_123'
        assert completed_order.paid_at is not None
        
        db_session.refresh(sample_user)
        assert sample_user.quota_balance == initial_quota + 10


def test_process_payment_invalid_status(app, db_session, sample_user):
    with app.app_context():
        order = OrderService.create_order(sample_user, '10_pack')
        OrderService.process_payment(order.id, 'test', 'TEST_123')
        
        with pytest.raises(ValueError, match='cannot process payment'):
            OrderService.process_payment(order.id, 'test', 'TEST_456')


def test_cancel_order(app, db_session, sample_user):
    with app.app_context():
        order = OrderService.create_order(sample_user, '10_pack')
        
        cancelled_order = OrderService.cancel_order(order.id)
        
        assert cancelled_order.status == 'cancelled'


def test_cancel_paid_order(app, db_session, sample_user):
    with app.app_context():
        order = OrderService.create_order(sample_user, '10_pack')
        OrderService.process_payment(order.id, 'test', 'TEST_123')
        
        with pytest.raises(ValueError, match='Paid order cannot be cancelled'):
            OrderService.cancel_order(order.id)


def test_get_user_orders(app, db_session, sample_user):
    with app.app_context():
        OrderService.create_order(sample_user, '10_pack')
        OrderService.create_order(sample_user, '50_pack')
        
        orders, total = OrderService.get_user_orders(sample_user, page=1, per_page=10)
        
        assert total == 2
        assert len(orders) == 2
