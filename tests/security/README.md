# Security Test Suite

This directory contains comprehensive security tests for SwiftBudget application.

## Test Categories

### 1. SQL Injection Tests (`test_sql_injection.py`)
Tests to ensure the application is protected against SQL injection attacks:
- Login form SQL injection attempts
- Signup form SQL injection attempts
- Transaction description SQL injection
- Category name SQL injection
- Search/filter parameter SQL injection
- Numeric field SQL injection
- ORDER BY clause SQL injection
- Database integrity verification

**Run:** `pytest tests/security/test_sql_injection.py -v`

### 2. XSS Attack Tests (`test_xss_attacks.py`)
Tests to ensure proper sanitization and XSS prevention:
- Script tag injection in various fields
- Event handler injection (onerror, onload, etc.)
- Stored XSS persistence
- Reflected XSS in URL parameters
- DOM-based XSS prevention
- HTML entity encoding
- JavaScript protocol prevention

**Run:** `pytest tests/security/test_xss_attacks.py -v`

### 3. Authentication Security Tests (`test_authentication.py`)
Tests for authentication security features:
- Account lockout after 5 failed attempts
- 15-minute lockout duration
- Failed attempt counter reset on success
- Automatic lockout expiration
- Password complexity requirements (12+ chars, uppercase, lowercase, number, symbol)
- Session timeout configuration (2 hours)
- Session cookie security flags
- Open redirect prevention
- Password hashing verification

**Run:** `pytest tests/security/test_authentication.py -v`

### 4. Input Validation Tests (`test_input_validation.py`)
Tests for input validation and overflow prevention:
- Decimal overflow prevention (max 9,999,999.99)
- Decimal precision validation (2 decimal places)
- Negative amount rejection
- Zero amount rejection
- Quantity overflow prevention
- Budget amount validation
- Alert threshold validation (0-100)
- String length validation
- Email format validation
- Date validation
- Invalid category/type rejection

**Run:** `pytest tests/security/test_input_validation.py -v`

### 5. Rate Limiting Tests (`test_rate_limiting.py`)
Tests for rate limiting enforcement:
- Login rate limit (5/minute, 20/hour)
- Signup rate limit (5/minute, 20/hour)
- Per-IP rate limiting
- Rate limit bypass prevention
- Rate limit configuration verification

**Run:** `pytest tests/security/test_rate_limiting.py -v`

## Running All Security Tests

```bash
# Run all security tests
pytest tests/security/ -v

# Run with coverage
pytest tests/security/ --cov=app --cov-report=html

# Run specific test class
pytest tests/security/test_sql_injection.py::TestSQLInjection -v

# Run specific test
pytest tests/security/test_authentication.py::TestAuthenticationSecurity::test_account_lockout_after_failed_attempts -v
```

## Test Requirements

All security tests require:
- Active virtual environment
- Database migrations applied
- Test fixtures from `conftest.py`
- CSRF disabled in testing config

## Expected Results

All security tests should **PASS**, indicating:
- ✅ No SQL injection vulnerabilities
- ✅ No XSS vulnerabilities
- ✅ Proper authentication security
- ✅ Input validation working correctly
- ✅ Rate limiting enforced

## Failure Investigation

If tests fail:

1. **SQL Injection Failures:**
   - Check that all queries use SQLAlchemy ORM
   - Verify parameterized queries
   - Check for raw SQL usage

2. **XSS Failures:**
   - Verify Jinja2 auto-escaping is enabled
   - Check for `|safe` filter usage
   - Ensure SafeString validator is applied

3. **Authentication Failures:**
   - Verify User model has security fields
   - Check database migration applied
   - Verify password validators imported

4. **Input Validation Failures:**
   - Check DecimalRange validator is applied
   - Verify form validators are correct
   - Check max values in forms

5. **Rate Limiting Failures:**
   - Verify Flask-Limiter is installed
   - Check rate limit decorators on routes
   - Verify limiter configuration

## Security Test Coverage

Current coverage:
- **SQL Injection:** 15 test cases
- **XSS Attacks:** 14 test cases
- **Authentication:** 18 test cases
- **Input Validation:** 15 test cases
- **Rate Limiting:** 12 test cases

**Total:** 74 security test cases

## Adding New Security Tests

When adding new features, add corresponding security tests:

1. Create test file in `tests/security/`
2. Follow naming convention: `test_<feature>_security.py`
3. Test all user input vectors
4. Test edge cases and boundary conditions
5. Update this README

## Security Testing Best Practices

1. **Test malicious input** - Don't just test valid cases
2. **Test edge cases** - Boundary values, overflow, underflow
3. **Test bypass attempts** - Try to circumvent security measures
4. **Verify error handling** - Ensure errors don't leak sensitive info
5. **Test combinations** - Multiple attack vectors together

## Integration with CI/CD

These tests should run:
- On every pull request
- Before deployment
- On a schedule (weekly)

Recommended CI/CD configuration:
```yaml
security-tests:
  script:
    - pytest tests/security/ -v --cov=app
  only:
    - merge_requests
    - main
```

## Reporting Security Issues

If you discover a security vulnerability:
1. **DO NOT** create a public issue
2. Contact the security team directly
3. Provide detailed reproduction steps
4. Include test case if possible

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)

---

**Last Updated:** March 4, 2026  
**Test Suite Version:** 1.0  
**Coverage:** 74 test cases across 5 categories
