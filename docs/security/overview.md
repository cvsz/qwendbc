# Security Guide

This document outlines security policies, best practices, and procedures for QwenDBC.

## Table of Contents

- [Security Overview](#security-overview)
- [Vulnerability Management](#vulnerability-management)
- [Access Control](#access-control)
- [Data Privacy](#data-privacy)
- [Secure Configuration](#secure-configuration)
- [Incident Response](#incident-response)
- [Compliance](#compliance)

---

## Security Overview

### Security Principles

QwenDBC follows these core security principles:

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions required
3. **Privacy by Design**: Data protection built into architecture
4. **Local-First**: Processing happens on your infrastructure
5. **Transparency**: Open source code for auditability

### Architecture Security

```
┌─────────────────────────────────────────┐
│         Network Security Layer          │
│  - Firewall Rules                       │
│  - Rate Limiting                        │
│  - DDoS Protection                      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│       Application Security Layer        │
│  - Input Validation                     │
│  - Authentication/Authorization         │
│  - Session Management                   │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          Data Security Layer            │
│  - Encryption at Rest                   │
│  - Secure Storage                       │
│  - Access Logging                       │
└─────────────────────────────────────────┘
```

---

## Vulnerability Management

### Current Security Advisories

#### Critical Vulnerabilities (Fixed)

**ChromaDB Code Injection** (CVE-2024-XXXXX)
- **Status**: ✅ Fixed in chromadb>=0.6.0
- **Impact**: Pre-authentication code execution
- **Mitigation**: Updated to secure version

**llama-cpp-python SSTI** (CVE-2024-XXXXX)
- **Status**: ✅ Fixed in llama-cpp-python>=0.3.8
- **Impact**: Remote code execution via model metadata
- **Mitigation**: Updated to secure version

**python-jose Algorithm Confusion** (CVE-2024-XXXXX)
- **Status**: ✅ Fixed in python-jose>=3.5.0
- **Impact**: JWT signature bypass
- **Mitigation**: Updated to secure version

#### High Vulnerabilities (Fixed)

**python-multipart Arbitrary File Write**
- **Status**: ✅ Fixed in python-multipart>=0.0.20
- **Impact**: File system compromise
- **Mitigation**: Updated to secure version

**ChromaDB Authorization Bypass**
- **Status**: ✅ Fixed in chromadb>=0.6.0
- **Impact**: Unauthorized data access
- **Mitigation**: Updated to secure version

### Dependency Scanning

Automated scanning is performed via:

1. **Dependabot**: Daily dependency checks
2. **GitHub CodeQL**: Static analysis on commits
3. **Safety**: Python vulnerability scanning
4. **npm audit**: JavaScript vulnerability checks

### Reporting Vulnerabilities

**To report a security vulnerability:**

1. **DO NOT** create public GitHub issues
2. Email: security@qwendbc.example.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if available)

**Response Timeline:**
- Acknowledgment: Within 48 hours
- Assessment: Within 5 business days
- Fix deployment: Based on severity

---

## Access Control

### Authentication

#### Current Implementation

The application currently supports local deployment without authentication. For production use:

**JWT Authentication Setup:**

```python
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

#### Recommended Authentication Flow

```
User Registration → Password Hash → Store Hash
User Login → Verify Password → Issue JWT
API Request → Validate JWT → Grant Access
```

### Authorization

#### Role-Based Access Control (RBAC)

Planned roles:
- **Admin**: Full system access
- **User**: Chat and model usage
- **Viewer**: Read-only access

#### API Access Control

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    # Validate token and return user
```

### Session Management

- JWT tokens expire after 30 minutes (configurable)
- Refresh tokens for extended sessions
- Token blacklisting for logout
- Secure cookie flags (HttpOnly, Secure, SameSite)

---

## Data Privacy

### Data Collection

QwenDBC minimizes data collection:

**Not Collected:**
- ❌ User chat content (stored locally only)
- ❌ Personal identifiers
- ❌ Usage analytics
- ❌ IP addresses (unless logged for security)

**May Be Stored Locally:**
- ✅ Chat history (user-controlled)
- ✅ Model files
- ✅ Application logs

### Data Storage

#### Local Storage

All data stored locally:
- Models: `./models/`
- Vector database: `./chroma_db/`
- Logs: `./logs/`

#### Data Retention

User-configurable retention:
- Chat history: Until manually cleared
- Logs: Rotated after 14 days
- Models: Until deleted

### Data Transmission

**In Transit:**
- HTTPS/TLS encryption (production)
- No data sent to external services
- Local network only (default)

**At Rest:**
- File system permissions
- Optional disk encryption
- Volume isolation (Docker)

### GDPR Compliance

For EU users:
- Right to access personal data
- Right to rectification
- Right to erasure ("right to be forgotten")
- Data portability
- Consent management

---

## Secure Configuration

### Production Checklist

#### Environment Variables

```env
# MUST CHANGE in production
SECRET_KEY=<strong-random-key>
DEBUG=False

# Restrict access
ALLOWED_ORIGINS=["https://your-domain.com"]

# Secure headers
CORS_ALLOW_CREDENTIALS=True
```

#### Docker Security

```yaml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"  # Non-root user
```

#### Network Security

```bash
# Firewall rules (UFW example)
sudo ufw allow from 127.0.0.1 to any port 8000
sudo ufw allow from 127.0.0.1 to any port 3000
sudo ufw enable
```

### Security Headers

Configure in reverse proxy:

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Strict-Transport-Security "max-age=31536000" always;
```

### Secret Management

**Never commit secrets to version control!**

Use environment variables or secret managers:

```bash
# Generate secure secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Store in environment
export SECRET_KEY="<generated-secret>"

# Or use Docker secrets
echo "<secret>" | docker secret create qwendbc_secret -
```

---

## Incident Response

### Security Incident Categories

**Severity Levels:**

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | Active exploitation | Immediate |
| P1 | Critical vulnerability | < 4 hours |
| P2 | High vulnerability | < 24 hours |
| P3 | Medium vulnerability | < 72 hours |
| P4 | Low vulnerability | < 1 week |

### Incident Response Process

```
1. Detection → 2. Containment → 3. Eradication → 4. Recovery → 5. Lessons Learned
```

#### Step 1: Detection

Sources:
- Automated alerts (Dependabot, CodeQL)
- User reports
- Security researcher disclosures
- Log analysis

#### Step 2: Containment

Immediate actions:
- Isolate affected systems
- Revoke compromised credentials
- Block malicious IPs
- Preserve evidence

#### Step 3: Eradication

Remove threat:
- Patch vulnerabilities
- Remove malware
- Update dependencies
- Reset credentials

#### Step 4: Recovery

Restore operations:
- Deploy patched versions
- Restore from clean backups
- Monitor for reinfection
- Verify functionality

#### Step 5: Lessons Learned

Post-incident:
- Document timeline
- Identify root cause
- Update procedures
- Implement preventive measures

### Contact Information

**Security Team:**
- Email: security@qwendbc.example.com
- PGP Key: [Available on request]

**Emergency Contacts:**
- Primary: security-lead@qwendbc.example.com
- Secondary: cto@qwendbc.example.com

---

## Compliance

### Standards Alignment

QwenDBC aligns with:

- **OWASP Top 10**: Web application security
- **CIS Benchmarks**: System hardening
- **NIST CSF**: Cybersecurity framework
- **GDPR**: Data protection (EU)
- **CCPA**: Consumer privacy (California)

### Audit Trail

Maintain logs for:
- Authentication attempts
- Authorization decisions
- Configuration changes
- Security events

Log format:
```json
{
  "timestamp": "2025-01-07T12:00:00Z",
  "event": "login_attempt",
  "user": "admin",
  "ip": "192.168.1.1",
  "result": "success",
  "details": {}
}
```

### Third-Party Audits

Recommended:
- Annual penetration testing
- Quarterly vulnerability scans
- Continuous dependency monitoring
- Code review before major releases

---

## Security Best Practices

### For Administrators

1. **Keep Systems Updated**
   - Regular OS patches
   - Dependency updates
   - Docker image rebuilds

2. **Monitor Continuously**
   - Log aggregation
   - Alert configuration
   - Anomaly detection

3. **Backup Regularly**
   - Automated backups
   - Off-site storage
   - Recovery testing

4. **Restrict Access**
   - Principle of least privilege
   - Network segmentation
   - Multi-factor authentication

### For Developers

1. **Secure Coding**
   - Input validation
   - Output encoding
   - Error handling

2. **Dependency Management**
   - Pin versions
   - Review updates
   - Remove unused packages

3. **Testing**
   - Security unit tests
   - Integration testing
   - Penetration testing

4. **Documentation**
   - Security procedures
   - Threat models
   - Incident response plans

### For Users

1. **Configuration**
   - Change default passwords
   - Enable HTTPS
   - Restrict network access

2. **Operations**
   - Regular updates
   - Monitor logs
   - Backup data

3. **Awareness**
   - Security advisories
   - Best practices
   - Incident reporting

---

## Security Resources

### Tools

- **Dependabot**: Dependency updates
- **CodeQL**: Static analysis
- **Safety**: Python vulnerabilities
- **npm audit**: JavaScript vulnerabilities
- **Trivy**: Container scanning

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NVD Database](https://nvd.nist.gov/)
- [GitHub Security Advisories](https://github.com/advisories)

### Training

- Secure coding courses
- Security awareness programs
- Incident response drills

---

*Last updated: January 2025*
*Version: 1.0.0*

**Security Status**: All known critical and high vulnerabilities have been addressed. See [SECURITY.md](../SECURITY.md) for reporting procedures.
