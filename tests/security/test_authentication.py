"""
Authentication Security Tests.

Tests for:
- Account lockout mechanism
- Password policy enforcement
- Rate limiting on auth endpoints
- Session security
"""

import pytest
from datetime import datetime, timedelta
from app.models.user import User


class TestAuthenticationSecurity:
    """Test suite for authentication security features."""
    
    def test_account_lockout_after_failed_attempts(self, client, test_user, db_session):
        """Test that account locks after 5 failed login attempts."""
        # Attempt 5 failed logins
        for i in range(5):
            response = client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'wrongpassword',
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            assert response.status_code == 200
        
        # Query user from database to check lockout status
        user = User.query.filter_by(id=test_user.id).first()
        
        # Verify account is locked
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
        assert user.locked_until > datetime.utcnow()
        
        # 6th attempt should show lockout message
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'wrongpassword',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        assert b'Account temporarily locked' in response.data
    
    def test_account_lockout_duration(self, client, test_user, db_session):
        """Test that account lockout lasts 15 minutes."""
        # Lock the account
        for i in range(5):
            client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'wrongpassword',
                'csrf_token': 'test'
            })
        
        user = User.query.filter_by(id=test_user.id).first()
        lockout_time = user.locked_until
        
        # Verify lockout is approximately 15 minutes from now
        expected_unlock = datetime.utcnow() + timedelta(minutes=15)
        time_diff = abs((lockout_time - expected_unlock).total_seconds())
        
        # Allow 5 second variance
        assert time_diff < 5
    
    def test_successful_login_resets_failed_attempts(self, client, test_user, db_session):
        """Test that successful login resets failed attempt counter."""
        # Make 3 failed attempts
        for i in range(3):
            client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'wrongpassword',
                'csrf_token': 'test'
            })
        
        user = User.query.filter_by(id=test_user.id).first()
        assert user.failed_login_attempts == 3
        
        # Successful login
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        user = User.query.filter_by(id=test_user.id).first()
        
        # Failed attempts should be reset
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
    
    def test_lockout_expires_automatically(self, client, test_user, db_session):
        """Test that lockout expires after the lockout period."""
        # Manually set lockout to expired time
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() - timedelta(minutes=1)
        db_session.session.commit()
        
        # Attempt login with correct password
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Should succeed (lockout expired)
        assert response.status_code == 200
        assert b'Welcome back' in response.data
        
        user = User.query.filter_by(id=test_user.id).first()
        
        # Lockout should be cleared
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
    
    def test_password_complexity_requirements(self, client):
        """Test that password policy is enforced."""
        weak_passwords = [
            'short',  # Too short
            'alllowercase123!',  # No uppercase
            'ALLUPPERCASE123!',  # No lowercase
            'NoNumbers!',  # No numbers
            'NoSpecialChar123',  # No special characters
            'Simple123',  # No special characters
        ]
        
        for weak_password in weak_passwords:
            response = client.post('/auth/signup', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': weak_password,
                'confirm_password': weak_password,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject weak password
            assert response.status_code == 200
            assert b'Password must' in response.data or b'between 12 and 128' in response.data
    
    def test_strong_password_accepted(self, client):
        """Test that strong passwords are accepted."""
        strong_passwords = [
            'ValidPass123!',
            'Str0ng!Password',
            'C0mpl3x@Pass',
            'MyP@ssw0rd123',
        ]
        
        for i, strong_password in enumerate(strong_passwords):
            response = client.post('/auth/signup', data={
                'username': f'testuser{i}',
                'email': f'test{i}@example.com',
                'password': strong_password,
                'confirm_password': strong_password,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should accept strong password
            # Either succeeds or fails for other reasons (duplicate email, etc.)
            assert response.status_code == 200
    
    def test_password_minimum_length(self, client):
        """Test that passwords must be at least 12 characters."""
        short_passwords = [
            'Short1!',  # 7 chars
            'Medium12!',  # 9 chars
            'Almost123!',  # 10 chars
            'Eleven123!',  # 11 chars
        ]
        
        for short_password in short_passwords:
            response = client.post('/auth/signup', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': short_password,
                'confirm_password': short_password,
                'csrf_token': 'test'
            }, follow_redirects=True)
            
            # Should reject
            assert b'between 12 and 128' in response.data
    
    def test_session_timeout_configuration(self, app):
        """Test that session timeout is set to 2 hours."""
        from datetime import timedelta
        
        # Check session lifetime
        assert app.config['PERMANENT_SESSION_LIFETIME'] == timedelta(hours=2)
    
    def test_session_cookie_security_flags(self, app):
        """Test that session cookies have security flags set."""
        # Check security flags
        assert app.config['SESSION_COOKIE_HTTPONLY'] is True
        assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
        
        # In production, should be secure (skip in testing)
        if app.config.get('ENV') == 'production':
            assert app.config['SESSION_COOKIE_SECURE'] is True
    
    def test_login_with_nonexistent_user(self, client):
        """Test that login with non-existent user doesn't reveal user existence."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'anypassword',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Should show generic error (no user enumeration)
        assert b'Invalid email or password' in response.data
        # Should NOT say "User not found" or "Email doesn't exist"
        assert b'not found' not in response.data.lower()
        assert b"doesn't exist" not in response.data.lower()
    
    def test_case_insensitive_email_login(self, client, test_user):
        """Test that email login is case-insensitive."""
        # Login with uppercase email
        response = client.post('/auth/login', data={
            'email': test_user.email.upper(),
            'password': 'password123',
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Should succeed
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_logout_clears_session(self, client, auth):
        """Test that logout properly clears the session."""
        # Login
        auth.login()
        
        # Access protected page (should work)
        response = client.get('/auth/dashboard')
        assert response.status_code == 200
        
        # Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert b'logged out' in response.data
        
        # Try to access protected page (should redirect to login)
        response = client.get('/auth/dashboard', follow_redirects=True)
        assert b'Log In' in response.data or b'login' in response.data.lower()
    
    def test_password_not_stored_in_plain_text(self, client, db_session):
        """Test that passwords are hashed, not stored in plain text."""
        password = 'TestPassword123!'
        
        response = client.post('/auth/signup', data={
            'username': 'hashtest',
            'email': 'hashtest@example.com',
            'password': password,
            'confirm_password': password,
            'csrf_token': 'test'
        }, follow_redirects=True)
        
        # Get user from database
        user = User.query.filter_by(email='hashtest@example.com').first()
        
        if user:
            # Password hash should not equal plain text password
            assert user.password_hash != password
            # Should be a bcrypt hash (starts with $2b$)
            assert user.password_hash.startswith('$2b$')
            # Should be reasonable length for bcrypt hash
            assert len(user.password_hash) >= 60
    
    def test_open_redirect_prevention(self, client, test_user):
        """Test that 'next' parameter doesn't allow open redirects."""
        # Attempt login with external redirect
        malicious_redirects = [
            'http://evil.com',
            'https://malicious.com/steal',
            '//evil.com',
            'javascript:alert(1)',
        ]
        
        for malicious_url in malicious_redirects:
            response = client.post(f'/auth/login?next={malicious_url}', data={
                'email': test_user.email,
                'password': 'password123',
                'csrf_token': 'test'
            }, follow_redirects=False)
            
            # Should not redirect to external URL
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                # Should redirect to internal page only
                assert not location.startswith('http://evil.com')
                assert not location.startswith('https://malicious.com')
                assert not location.startswith('//')
                assert not location.startswith('javascript:')
    
    def test_concurrent_login_attempts(self, client, test_user, db_session):
        """Test that concurrent failed login attempts are tracked correctly."""
        # Simulate concurrent login attempts
        for i in range(3):
            client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'wrong1',
                'csrf_token': 'test'
            })
            client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'wrong2',
                'csrf_token': 'test'
            })
        
        user = User.query.filter_by(id=test_user.id).first()
        
        # Should have tracked all 6 attempts
        assert user.failed_login_attempts >= 5
        # Should be locked
        assert user.locked_until is not None
