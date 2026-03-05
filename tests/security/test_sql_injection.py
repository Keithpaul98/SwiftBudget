"""
SQL Injection Security Tests.

Tests to ensure the application is protected against SQL injection attacks.
All database queries should use parameterized queries via SQLAlchemy ORM.
"""

import pytest
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category


class TestSQLInjection:
    """Test suite for SQL injection vulnerabilities."""
    
    def test_login_sql_injection_attempt(self, client):
        """
        Test that SQL injection in login form is prevented.
        
        Common SQL injection patterns:
        - ' OR '1'='1
        - admin'--
        - ' OR 1=1--
        """
        malicious_inputs = [
            "' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
            "'; DROP TABLE users;--",
            "1' UNION SELECT NULL--",
        ]
        
        for malicious_email in malicious_inputs:
            response = client.post('/auth/login', data={
                'email': malicious_email,
                'password': 'anypassword',
                'csrf_token': 'test'  # CSRF disabled in testing
            }, follow_redirects=True)
            
            # Should not crash or expose SQL errors
            assert response.status_code == 200
            # Should show invalid login or validation error message
            assert (b'Invalid email or password' in response.data or 
                    b'Email is required' in response.data or
                    b'Invalid' in response.data or
                    b'Log In' in response.data)
    
    def test_signup_sql_injection_attempt(self, client):
        """Test that SQL injection in signup form is prevented."""
        malicious_inputs = [
            "test'; DROP TABLE users;--",
            "admin'--",
            "' OR '1'='1",
        ]
        
        for malicious_username in malicious_inputs:
            response = client.post('/auth/signup', data={
                'username': malicious_username,
                'email': 'test@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should not crash
            assert response.status_code == 200
            # Either succeeds with sanitized input or fails validation
            # But should never execute SQL injection
    
    def test_transaction_description_sql_injection(self, client, auth, test_user, test_category):
        """Test SQL injection in transaction description field."""
        auth.login()
        
        malicious_descriptions = [
            "'; DROP TABLE transactions;--",
            "Test' OR '1'='1",
            "'; UPDATE transactions SET amount=0;--",
        ]
        
        for malicious_desc in malicious_descriptions:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'description': malicious_desc,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should not crash
            assert response.status_code == 200
            
            # Verify transactions table still exists
            transactions = Transaction.query.all()
            assert transactions is not None
    
    def test_category_name_sql_injection(self, client, auth, test_user):
        """Test SQL injection in category name field."""
        auth.login()
        
        malicious_names = [
            "Food'; DROP TABLE categories;--",
            "' OR '1'='1",
            "Test'; DELETE FROM categories;--",
        ]
        
        for malicious_name in malicious_names:
            response = client.post('/categories/create', data={
                'name': malicious_name,
                'type': 'expense',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should handle gracefully
            assert response.status_code in [200, 302, 404]
            
            # Verify categories table still exists
            categories = Category.query.all()
            assert categories is not None
    
    def test_search_filter_sql_injection(self, client, auth, test_user):
        """Test SQL injection in search/filter parameters."""
        auth.login()
        
        malicious_params = [
            "' OR '1'='1",
            "1; DROP TABLE transactions;--",
            "' UNION SELECT * FROM users;--",
        ]
        
        for malicious_param in malicious_params:
            # Test category filter
            response = client.get(f'/transactions?category_id={malicious_param}')
            assert response.status_code in [200, 308, 400, 404]
            
            # Test transaction type filter
            response = client.get(f'/transactions?transaction_type={malicious_param}')
            assert response.status_code in [200, 308, 400, 404]
    
    def test_user_query_by_email_sql_injection(self, client, db_session):
        """Test that user lookup by email is safe from SQL injection."""
        # This tests the internal query mechanism
        malicious_emails = [
            "test@example.com' OR '1'='1",
            "'; DROP TABLE users;--",
        ]
        
        for malicious_email in malicious_emails:
            # Should return None or valid user, never crash
            user = User.query.filter_by(email=malicious_email).first()
            # If user exists, it should be a valid User object
            if user:
                assert isinstance(user, User)
    
    def test_transaction_query_sql_injection(self, client, auth, test_user, db_session):
        """Test that transaction queries are safe from SQL injection."""
        auth.login()
        
        # Attempt to inject SQL through transaction ID
        malicious_ids = [
            "1 OR 1=1",
            "1; DROP TABLE transactions;",
            "1' UNION SELECT * FROM users--",
        ]
        
        for malicious_id in malicious_ids:
            response = client.get(f'/transactions/{malicious_id}/edit')
            # Should return 404 or 400, not crash
            assert response.status_code in [200, 400, 404]
    
    def test_numeric_field_sql_injection(self, client, auth, test_user, test_category):
        """Test SQL injection attempts in numeric fields."""
        auth.login()
        
        malicious_amounts = [
            "100'; DROP TABLE transactions;--",
            "100 OR 1=1",
            "100; DELETE FROM transactions;",
        ]
        
        for malicious_amount in malicious_amounts:
            response = client.post('/transactions/create', data={
                'amount': malicious_amount,
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should fail validation, not execute SQL
            assert response.status_code in [200, 308]
            # Should show validation error
            assert b'Invalid' in response.data or b'required' in response.data
    
    def test_order_by_sql_injection(self, client, auth, test_user):
        """Test SQL injection in ORDER BY clauses."""
        auth.login()
        
        malicious_sort = [
            "amount; DROP TABLE transactions;--",
            "date' OR '1'='1",
            "id, (SELECT * FROM users)",
        ]
        
        for malicious_param in malicious_sort:
            response = client.get(f'/transactions?sort={malicious_param}')
            # Should handle gracefully; 308 is permanent redirect
            assert response.status_code in [200, 308, 400, 404]
    
    def test_database_integrity_after_injection_attempts(self, client, auth, test_user, db_session):
        """
        Verify database integrity after multiple injection attempts.
        
        This is a comprehensive test to ensure no tables were dropped
        or data was corrupted during injection attempts.
        """
        auth.login()
        
        # Attempt multiple injection attacks
        injection_payloads = [
            "'; DROP TABLE users;--",
            "'; DROP TABLE transactions;--",
            "'; DROP TABLE categories;--",
            "'; DELETE FROM users;--",
        ]
        
        for payload in injection_payloads:
            # Try in various fields
            client.post('/auth/login', data={
                'email': payload,
                'password': 'test',
                'csrf_token': 'test'
            })
            
            client.post('/transactions/create', data={
                'amount': '100',
                'description': payload,
                'csrf_token': 'test'
            })
        
        # Verify all tables still exist and are queryable
        users = User.query.all()
        transactions = Transaction.query.all()
        categories = Category.query.all()
        
        assert users is not None
        assert transactions is not None
        assert categories is not None
        
        # Verify test user still exists
        user = User.query.filter_by(id=test_user.id).first()
        assert user is not None
        assert user.username == test_user.username
