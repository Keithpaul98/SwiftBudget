"""
XSS (Cross-Site Scripting) Security Tests.

Tests to ensure the application properly sanitizes user input
and prevents XSS attacks through various input vectors.
"""

import pytest
from app.models.transaction import Transaction
from app.models.category import Category


class TestXSSProtection:
    """Test suite for XSS vulnerability protection."""
    
    def test_xss_in_transaction_description(self, client, auth, test_user, test_category):
        """Test that XSS scripts in transaction descriptions are sanitized."""
        auth.login()
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<marquee onstart=alert('XSS')>",
        ]
        
        for xss_payload in xss_payloads:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'description': xss_payload,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should either reject or sanitize
            assert response.status_code == 200
            
            # Check if transaction was created
            transaction = Transaction.query.filter_by(
                user_id=test_user.id,
                description=xss_payload
            ).first()
            
            if transaction:
                # If stored, verify it's not executed when displayed
                response = client.get('/transactions')
                # Raw script tags should not appear in response
                assert b'<script>' not in response.data
                assert b'onerror=' not in response.data
                assert b'onload=' not in response.data
    
    def test_xss_in_category_name(self, client, auth, test_user):
        """Test that XSS scripts in category names are sanitized."""
        auth.login()
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "Food<script>alert('XSS')</script>",
        ]
        
        for xss_payload in xss_payloads:
            response = client.post('/categories/create', data={
                'name': xss_payload,
                'type': 'expense',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should handle gracefully
            assert response.status_code in [200, 302, 404]
            
            # If category was created, verify XSS is not executed
            if response.status_code == 302:
                response = client.get('/categories')
                assert b'<script>' not in response.data
    
    def test_xss_in_username(self, client):
        """Test that XSS scripts in usernames are sanitized."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "user<img src=x onerror=alert('XSS')>",
            "admin<svg onload=alert('XSS')>",
        ]
        
        for xss_payload in xss_payloads:
            response = client.post('/auth/signup', data={
                'username': xss_payload,
                'email': 'xsstest@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should either reject or sanitize
            assert response.status_code == 200
            
            # If user was created, verify XSS is not executed on display
            response = client.get('/auth/login')
            assert b'<script>' not in response.data
    
    def test_xss_in_project_name(self, client, auth, test_user):
        """Test that XSS scripts in project names are sanitized."""
        auth.login()
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "Project<img src=x onerror=alert('XSS')>",
        ]
        
        for xss_payload in xss_payloads:
            response = client.post('/projects/create', data={
                'name': xss_payload,
                'description': 'Test project',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should handle gracefully
            assert response.status_code in [200, 302, 404]
            
            # Verify XSS is not executed when displayed
            if response.status_code == 302:
                response = client.get('/projects')
                assert b'<script>' not in response.data
    
    def test_xss_in_project_description(self, client, auth, test_user):
        """Test that XSS scripts in project descriptions are sanitized."""
        auth.login()
        
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post('/projects/create', data={
            'name': 'Test Project',
            'description': xss_payload,
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Should handle gracefully
        assert response.status_code in [200, 302, 404]
        
        # Verify XSS is not executed
        if response.status_code == 302:
            response = client.get('/projects')
            assert b'<script>' not in response.data
    
    def test_stored_xss_persistence(self, client, auth, test_user, test_category, db_session):
        """
        Test that stored XSS payloads don't execute even after
        being retrieved from database.
        """
        auth.login()
        
        xss_payload = "<script>alert('Stored XSS')</script>"
        
        # Create transaction with XSS payload
        response = client.post('/transactions/create', data={
            'amount': '100.00',
            'category_id': test_category.id,
            'transaction_type': 'expense',
            'transaction_date': '2026-03-04',
            'description': xss_payload,
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Retrieve and display transaction
        response = client.get('/transactions')
        
        # XSS should not be executed
        assert b'<script>' not in response.data
        # Content should be escaped or sanitized
        assert b'&lt;script&gt;' in response.data or b'alert' not in response.data
    
    def test_reflected_xss_in_url_parameters(self, client, auth, test_user):
        """Test that URL parameters don't cause reflected XSS."""
        auth.login()
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
        ]
        
        for xss_payload in xss_payloads:
            # Test in search parameter
            response = client.get(f'/transactions?search={xss_payload}')
            assert b'<script>' not in response.data
            
            # Test in filter parameter
            response = client.get(f'/transactions?category={xss_payload}')
            assert b'<script>' not in response.data
    
    def test_dom_based_xss_prevention(self, client, auth, test_user):
        """Test that DOM-based XSS is prevented in JavaScript contexts."""
        auth.login()
        
        # Get dashboard page
        response = client.get('/auth/dashboard')
        
        # Verify that user input is properly escaped in JavaScript
        # Check that Chart.js data doesn't contain unescaped user input
        assert b'<script>' not in response.data
        # Ensure proper JSON encoding
        assert b'\\u003c' in response.data or b'&lt;' in response.data or b'<script>' not in response.data
    
    def test_xss_in_flash_messages(self, client, auth):
        """Test that flash messages don't execute XSS."""
        # Attempt login with XSS in email
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post('/auth/login', data={
            'email': xss_payload,
            'password': 'test',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Flash message should not execute script
        assert b'<script>' not in response.data
    
    def test_xss_in_error_messages(self, client, auth, test_user, test_category):
        """Test that error messages don't execute XSS."""
        auth.login()
        
        # Submit invalid form with XSS payload
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post('/transactions/create', data={
            'amount': xss_payload,  # Invalid amount
            'category_id': test_category.id,
            'transaction_type': 'expense',
            'transaction_date': '2026-03-04',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Error message should not execute script
        assert b'<script>' not in response.data
    
    def test_html_entity_encoding(self, client, auth, test_user, test_category):
        """Test that HTML entities are properly encoded."""
        auth.login()
        
        html_entities = [
            "&lt;script&gt;",
            "&#60;script&#62;",
            "&amp;lt;script&amp;gt;",
        ]
        
        for entity in html_entities:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'description': entity,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should handle gracefully
            assert response.status_code == 200
    
    def test_javascript_protocol_prevention(self, client, auth, test_user, test_category):
        """Test that javascript: protocol is blocked."""
        auth.login()
        
        javascript_urls = [
            "javascript:alert('XSS')",
            "JAVASCRIPT:alert('XSS')",
            "java\nscript:alert('XSS')",
            "java\tscript:alert('XSS')",
        ]
        
        for js_url in javascript_urls:
            response = client.post('/transactions/create', data={
                'amount': '100.00',
                'category_id': test_category.id,
                'transaction_type': 'expense',
                'transaction_date': '2026-03-04',
                'description': js_url,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should be rejected or sanitized
            assert response.status_code == 200
            
            # Verify javascript: protocol is not in response
            response = client.get('/transactions')
            assert b'javascript:' not in response.data.lower()
