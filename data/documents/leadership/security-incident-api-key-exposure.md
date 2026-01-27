# Security Incident Report: API Key Exposure

**Incident ID:** SEC-2024-003
**Version:** 1.0.0
**Date:** 2024-11-18
**Owner:** Security Team
**Status:** Resolved
**Classification:** CONFIDENTIAL

---

## CONFIDENTIAL DOCUMENT

This security incident report is strictly confidential. Access is limited to:
- Leadership Team
- Security Team
- Legal Team
- Authorized Administrators

**Do not share or discuss outside authorized channels.**

---

## Executive Summary

On November 15, 2024, a CloudSignal API key was discovered exposed in a public GitHub repository. The key belonged to a customer integration and provided read-only access to their metrics data. The incident was contained within 4 hours of discovery, with no evidence of unauthorized data access.

**Severity:** High
**Impact:** Potential customer data exposure
**Resolution:** API key revoked and rotated, customer notified

## Incident Timeline

| Time (UTC) | Event |
|------------|-------|
| 2024-11-15 09:23 | GitHub secret scanning alert received |
| 2024-11-15 09:31 | Security team acknowledges alert |
| 2024-11-15 09:45 | API key identified, customer determined |
| 2024-11-15 10:02 | API key revoked in production |
| 2024-11-15 10:15 | Customer integration team contacted |
| 2024-11-15 11:30 | Customer acknowledged, new key issued |
| 2024-11-15 13:22 | Customer confirmed new key working |
| 2024-11-15 14:00 | Access logs reviewed, no unauthorized access found |

## Technical Details

### Exposed Credential

| Attribute | Value |
|-----------|-------|
| Key Type | Customer API Key |
| Permissions | Read-only (metrics:read, alerts:read) |
| Customer | Acme Corp (customer_id: cust_acme_001) |
| Exposure Location | github.com/acme-corp/internal-tools |
| Commit Date | 2024-11-12 |
| Days Exposed | ~3 days |

### Access Log Analysis

Review of API access logs for the exposed key:

| Metric | Value |
|--------|-------|
| Total API calls (Nov 12-15) | 1,247 |
| Unique IP addresses | 3 |
| Known IPs (Acme Corp) | 3 |
| Unknown IPs | 0 |
| Anomalous requests | 0 |

**Conclusion:** No evidence of unauthorized access during exposure window.

## Root Cause Analysis

### Primary Cause

An Acme Corp developer accidentally committed the API key to a private repository that was later made public during a code cleanup initiative.

### Contributing Factors

1. **Customer education gap:** Integration documentation didn't emphasize secret management best practices
2. **Detection delay:** 3-day gap between commit and detection (within GitHub scanning SLA)
3. **Key permissions:** Read-only scope limited potential impact

## Impact Assessment

### Data at Risk

If the key had been exploited, the attacker could have accessed:

- Acme Corp's metrics data (last 30 days)
- Alert configurations
- Dashboard definitions

### Data NOT at Risk

The exposed key did not provide access to:

- Other customers' data (tenant isolation confirmed)
- Write operations (alerts, configurations)
- PII or financial data
- CloudSignal internal systems

### Business Impact

| Category | Impact | Notes |
|----------|--------|-------|
| Data breach | None confirmed | No unauthorized access detected |
| Customer trust | Low | Proactive communication appreciated |
| Regulatory | None | No PII exposed, no notification required |
| Financial | Minimal | ~8 hours engineering time |

## Remediation Actions

### Immediate (Completed)

| Action | Owner | Status |
|--------|-------|--------|
| Revoke exposed API key | Security | Completed |
| Issue new API key to customer | Support | Completed |
| Review access logs | Security | Completed |
| Notify customer | Account Manager | Completed |

### Short-term (In Progress)

| Action | Owner | Target Date |
|--------|-------|-------------|
| Add secret scanning to customer documentation | Docs Team | 2024-11-30 |
| Implement key expiration policy (90 days) | Engineering | 2024-12-15 |
| Create customer security checklist | Security | 2024-12-01 |

### Long-term (Planned)

| Action | Owner | Target Date |
|--------|-------|-------------|
| Implement key usage anomaly detection | Security | Q1 2025 |
| Customer security awareness program | Customer Success | Q1 2025 |
| Third-party secret scanning integration | Engineering | Q1 2025 |

## Lessons Learned

### What Worked Well

1. **GitHub secret scanning:** Detected exposure within reasonable timeframe
2. **Incident response:** Team mobilized quickly, key revoked in <40 minutes
3. **Customer communication:** Transparent, proactive notification maintained trust
4. **Scope limitation:** Read-only key reduced potential impact

### What Needs Improvement

1. **Customer education:** Need better documentation on secret management
2. **Key lifecycle:** Implement automatic key rotation/expiration
3. **Detection:** Consider real-time third-party scanning services
4. **Monitoring:** Add anomaly detection for API key usage patterns

## Communication Log

### Internal

| Date | Audience | Method | Content |
|------|----------|--------|---------|
| 2024-11-15 | Leadership | Slack | Initial alert and status |
| 2024-11-15 | Leadership | Email | Incident summary |
| 2024-11-18 | All-hands | Meeting | Lessons learned (sanitized) |

### External

| Date | Audience | Method | Content |
|------|----------|--------|---------|
| 2024-11-15 | Acme Corp (Tech) | Phone | Initial notification |
| 2024-11-15 | Acme Corp (Tech) | Email | New credentials |
| 2024-11-16 | Acme Corp (Exec) | Email | Incident summary |

## Regulatory Considerations

### GDPR

- **Applicable:** No (no EU personal data exposed)
- **Notification required:** No

### SOC 2

- **Applicable:** Yes
- **Finding:** Logged as security event, remediation documented
- **Auditor notification:** Not required (no control failure)

### Customer Contracts

- **Breach notification clause:** No (no actual breach occurred)
- **SLA impact:** None

## Appendix

### A. Incident Response Checklist Used

- [x] Acknowledge alert within 15 minutes
- [x] Identify scope and severity
- [x] Contain the threat (revoke credentials)
- [x] Notify stakeholders
- [x] Investigate root cause
- [x] Document timeline
- [x] Implement remediation
- [x] Conduct post-mortem

### B. Related Documents

- [Incident Response Runbook](/sre/runbooks/incident-response)
- [API Key Management Policy](/security/api-key-policy)
- [Customer Communication Templates](/legal/customer-incident-templates)

---

**Prepared by:** Security Team
**Reviewed by:** VP Engineering, Legal
**Approved by:** CEO

*This document is retained per CloudSignal's security incident retention policy (7 years).*
