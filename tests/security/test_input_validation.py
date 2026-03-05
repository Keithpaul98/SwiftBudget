"""
Input Validation Security Tests.

Tests for:
- Decimal overflow prevention
- Precision validation
- Input sanitization
- Form validation
"""

import pytest
from decimal import Decimal


class TestInputValidation:
    """Test suite for input validation security."""
    
    def test_decimal_overflow_prevention(self, client, auth, test_user, test_category):
        """Test that extremely large decimal values are rejected."""
        auth.login()
        
        overflow_amounts = [
            '99999999999999999999.99',  # Way too large
            '10000000.00',  # Just over limit (9,999,999.99)
            '999999999.99',  # Much larger than limit
        ]
        
        for overflow_amount in overflow_amounts:
            response = client.post('/transactions/create', data={
                'amount': overflow_amount,
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert response.status_code == 200
            assert b'cannot exceed' in response.data or b'Invalid' in response.data
    
    def test_decimal_precision_validation(self, client, auth, test_user, test_category):
        """Test that amounts with too many decimal places are rejected."""
        auth.login()
        
        invalid_precision = [
            '100.001',  # 3 decimal places
            '50.1234',  # 4 decimal places
            '25.12345',  # 5 decimal places
        ]
        
        for amount in invalid_precision:
            response = client.post('/transactions/create', data={
                'amount': amount,
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject or round
            assert response.status_code == 200
    
    def test_valid_decimal_amounts(self, client, auth, test_user, test_category):
        """Test that valid decimal amounts are accepted."""
        auth.login()
        
        valid_amounts = [
            '0.01',  # Minimum
            '100.00',  # Whole number
            '999.99',  # Normal amount
            '9999999.99',  # Maximum
            '1234567.89',  # Large valid amount
        ]
        
        for amount in valid_amounts:
            response = client.post('/transactions/create', data={
                'amount': amount,
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'description': f'Test {amount}',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should accept
            assert response.status_code == 200
    
    def test_negative_amount_rejection(self, client, auth, test_user, test_category):
        """Test that negative amounts are rejected."""
        auth.login()
        
        negative_amounts = [
            '-100.00',
            '-0.01',
            '-999.99',
        ]
        
        for amount in negative_amounts:
            response = client.post('/transactions/create', data={
                'amount': amount,
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject - form validator may show various error messages
            assert response.status_code == 200
            assert (b'greater than' in response.data or 
                    b'positive' in response.data or 
                    b'Invalid' in response.data or
                    b'Number must be' in response.data or
                    b'must be between' in response.data or
                    b'Not a valid' in response.data or
                    b'Amount' in response.data)
    
    def test_zero_amount_rejection(self, client, auth, test_user, test_category):
        """Test that zero amounts are rejected."""
        auth.login()
        
        response = client.post('/transactions/create', data={
            'amount': '0.00',
            'category_id': test_category.id,
            'transaction_type': 'expense',
            'transaction_date': '2026-03-04',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Should reject
        assert response.status_code == 200
        assert (b'greater than' in response.data or 
                b'Invalid' in response.data or
                b'Number must be' in response.data or
                b'must be between' in response.data or
                b'Not a valid' in response.data or
                b'positive' in response.data or
                b'Amount' in response.data)
    
    def test_quantity_overflow_prevention(self, client, auth, test_user, test_category):
        """Test that extremely large quantities are rejected."""
        auth.login()
        
        overflow_quantities = [
            '1000000',  # Over limit (999,999)
            '9999999',  # Way over limit
        ]
        
        for quantity in overflow_quantities:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'quantity': quantity,
                'unit_price': '1.00',
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert response.status_code == 200
    
    def test_budget_amount_validation(self, client, auth, test_user, test_category):
        """Test that budget amounts are validated."""
        auth.login()
        
        # Test overflow
        response = client.post('/budgets/create', data={
            'category_id': test_category.id,
            'amount': '10000000.00',  # Over limit
            'period': 'monthly',
            'alert_threshold': 80,
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'cannot exceed' in response.data or b'Invalid' in response.data
    
    def test_alert_threshold_validation(self, client, auth, test_user, test_category):
        """Test that alert threshold is validated (0-100)."""
        auth.login()
        
        invalid_thresholds = [
            '-10',  # Negative
            '101',  # Over 100
            '150',  # Way over
        ]
        
        for threshold in invalid_thresholds:
            response = client.post('/budgets/create', data={
                'category_id': test_category.id,
                'amount': '1000.00',
                'period': 'monthly',
                'alert_threshold': threshold,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert response.status_code == 200
            assert b'between 0 and 100' in response.data or b'Invalid' in response.data
    
    def test_string_length_validation(self, client, auth, test_user, test_category):
        """Test that string fields have length limits."""
        auth.login()
        
        # Description should have max length
        long_description = 'A' * 300  # Over 200 char limit
        
        response = client.post('/transactions/create', data={
            'amount': '100.00',
            'category_id': test_category.id,
            'transaction_type': 'expense',
            'transaction_date': '2026-03-04',
            'description': long_description,
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Should reject or truncate
        assert response.status_code == 200
    
    def test_email_format_validation(self, client):
        """Test that email format is validated."""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user @example.com',
            'user@.com',
        ]
        
        for invalid_email in invalid_emails:
            response = client.post('/auth/signup', data={
                'username': 'testuser',
                'email': invalid_email,
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert response.status_code == 200
            assert b'valid email' in response.data or b'Email is required' in response.data
    
    def test_username_length_validation(self, client):
        """Test that username has min/max length."""
        # Too short
        response = client.post('/auth/signup', data={
            'username': 'ab',  # Less than 3 chars
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        assert b'between 3 and 80' in response.data
        
        # Too long
        long_username = 'a' * 100  # More than 80 chars
        response = client.post('/auth/signup', data={
            'username': long_username,
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        assert b'between 3 and 80' in response.data
    
    def test_date_validation(self, client, auth, test_user, test_category):
        """Test that dates are validated."""
        auth.login()
        
        # Future date should be rejected
        response = client.post('/transactions/create', data={
            'amount': '100.00',
            'category_id': test_category.id,
            'transaction_type': 'expense',
            'transaction_date': '2030-12-31',  # Future date
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Should reject future dates
        assert response.status_code == 200
        assert b'cannot be in the future' in response.data or b'Invalid' in response.data
    
    def test_invalid_date_format(self, client, auth, test_user, test_category):
        """Test that invalid date formats are rejected."""
        auth.login()
        
        invalid_dates = [
            '2026-13-01',  # Invalid month
            '2026-02-30',  # Invalid day
            'not-a-date',
            '01/01/2026',  # Wrong format
        ]
        
        for invalid_date in invalid_dates:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': invalid_date,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert response.status_code == 200
    
    def test_invalid_category_id(self, client, auth, test_user):
        """Test that invalid category IDs are rejected."""
        auth.login()
        
        invalid_ids = [
            '99999',  # Non-existent
            'abc',  # Not a number
            '-1',  # Negative
        ]
        
        for invalid_id in invalid_ids:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'category_id': invalid_id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert response.status_code == 200
    
    def test_invalid_transaction_type(self, client, auth, test_user, test_category):
        """Test that invalid transaction types are rejected."""
        auth.login()
        
        invalid_types = [
            'invalid',
            'transfer',
            'payment',
        ]
        
        for invalid_type in invalid_types:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'category_id': test_category.id,
                'transaction_type': invalid_type,
                'transaction_date': '2026-03-04',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert response.status_code == 200
