import pytest
from services.quota_service import QuotaService
from models.quota_transaction import QuotaTransaction


def test_get_balance(app, db_session, sample_user):
    with app.app_context():
        balance = QuotaService.get_balance(sample_user)
        assert balance == 10


def test_check_sufficient_true(app, db_session, sample_user):
    with app.app_context():
        result = QuotaService.check_sufficient(sample_user, 'generate_image', 5)
        assert result is True


def test_check_sufficient_false(app, db_session, sample_user):
    with app.app_context():
        result = QuotaService.check_sufficient(sample_user, 'generate_image', 20)
        assert result is False


def test_consume_quota(app, db_session, sample_user):
    with app.app_context():
        initial_balance = sample_user.quota_balance
        
        transaction = QuotaService.consume(
            user=sample_user,
            action='generate_image',
            count=2,
            description='Test generation'
        )
        
        assert transaction.amount == -2
        assert transaction.type == 'consume'
        assert sample_user.quota_balance == initial_balance - 2
        assert transaction.balance_after == sample_user.quota_balance


def test_consume_insufficient_quota(app, db_session, sample_user):
    with app.app_context():
        with pytest.raises(ValueError, match='Insufficient quota'):
            QuotaService.consume(
                user=sample_user,
                action='generate_image',
                count=20
            )


def test_add_quota(app, db_session, sample_user):
    with app.app_context():
        initial_balance = sample_user.quota_balance
        
        transaction = QuotaService.add_quota(
            user=sample_user,
            amount=50,
            reason='Purchase 50 quota'
        )
        
        assert transaction.amount == 50
        assert transaction.type == 'gift'
        assert sample_user.quota_balance == initial_balance + 50


def test_refund_quota(app, db_session, sample_user):
    with app.app_context():
        consume_transaction = QuotaService.consume(
            user=sample_user,
            action='generate_image',
            count=3
        )
        
        balance_after_consume = sample_user.quota_balance
        
        refund_transaction = QuotaService.refund(
            transaction_id=consume_transaction.id,
            reason='Test refund'
        )
        
        assert refund_transaction.amount == 3
        assert refund_transaction.type == 'refund'
        assert sample_user.quota_balance == balance_after_consume + 3


def test_get_transactions(app, db_session, sample_user):
    with app.app_context():
        QuotaService.consume(sample_user, 'generate_image', 1)
        QuotaService.add_quota(sample_user, 10, 'Test add')
        
        transactions, total = QuotaService.get_transactions(sample_user, page=1, per_page=10)
        
        assert total == 2
        assert len(transactions) == 2
        assert transactions[0].created_at >= transactions[1].created_at


def test_quota_costs_rules(app, db_session, sample_user):
    with app.app_context():
        QuotaService.consume(sample_user, 'generate_outline', 1)
        assert sample_user.quota_balance == 10
        
        QuotaService.consume(sample_user, 'generate_description', 10)
        assert sample_user.quota_balance == 9
        
        QuotaService.consume(sample_user, 'generate_image', 2)
        assert sample_user.quota_balance == 7
        
        QuotaService.consume(sample_user, 'edit_image', 2)
        assert sample_user.quota_balance == 6
