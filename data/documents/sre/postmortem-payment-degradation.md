# Payment Service Degradation Analysis

**Incident ID:** INC-2024-1105
**Severity:** SEV-2 (Major)
**Duration:** 47 minutes
**Date:** November 5, 2024
**Author:** Alex Thompson, Senior SRE
**Status:** Active

## Executive Summary

On November 5, 2024, CloudSignal's payment processing service experienced severe latency degradation, with p99 response times increasing from 200ms to 8 seconds. This affected enterprise customers attempting to upgrade plans or update billing information. The root cause was a slow database query introduced in a recent deployment that lacked proper indexing.

## Impact

| Metric | Value |
|--------|-------|
| Duration | 47 minutes (2:15 PM - 3:02 PM EST) |
| Customers Affected | ~50 enterprise customers |
| Failed Transactions | 23 |
| Revenue Impact | $12,000 (delayed, not lost) |
| SLA Breach | Yes (payment SLA: 99.9%) |

### User Experience

- Payment page load time: 200ms → 8s
- Checkout timeout errors: 23 occurrences
- Billing page errors: "Request timeout" displayed

## Timeline (All times EST)

| Time | Event |
|------|-------|
| 1:45 PM | Deployment of billing-service v2.3.1 |
| 2:00 PM | Deployment validated, monitoring nominal |
| 2:15 PM | First customer support ticket: "Payment page slow" |
| 2:18 PM | Automated alert: "payment_service p99 > 2s" |
| 2:20 PM | On-call SRE (Alex) begins investigation |
| 2:25 PM | Identified: billing-service database queries slow |
| 2:30 PM | Query analysis reveals missing index |
| 2:35 PM | Decision: Rollback vs. hotfix |
| 2:40 PM | Initiated rollback to v2.3.0 |
| 2:55 PM | Rollback complete |
| 3:02 PM | Latency returned to normal, incident closed |

## Root Cause Analysis

### The Problematic Query

A new feature in v2.3.1 introduced a query to fetch subscription history:

```sql
-- Slow query (no index)
SELECT * FROM subscription_events
WHERE customer_id = $1
AND event_type IN ('upgrade', 'downgrade', 'renewal')
ORDER BY created_at DESC
LIMIT 100;
```

This query performed a full table scan on `subscription_events` (12M rows) instead of using an index.

### Why It Wasn't Caught

1. **Staging data volume:** Staging had 50K rows vs. 12M in production
2. **Query plan difference:** Index was used in staging (small table)
3. **No load testing:** Performance testing skipped due to "small change"
4. **Code review gap:** Reviewers didn't check query plans

### Performance Metrics

| Environment | Row Count | Query Time |
|-------------|-----------|------------|
| Staging | 50,000 | 15ms |
| Production | 12,000,000 | 7,800ms |

## Fix Applied

### Immediate (Rollback)

Rolled back to v2.3.0 to restore service.

### Permanent Fix (v2.3.2)

Added compound index:

```sql
CREATE INDEX CONCURRENTLY idx_subscription_events_customer_type_date
ON subscription_events (customer_id, event_type, created_at DESC);
```

Query time after fix: **12ms**

## Action Items

### Immediate (Completed)

| Action | Owner | Status |
|--------|-------|--------|
| Rollback to v2.3.0 | @alex | Done |
| Create index in production | @alex | Done |
| Redeploy v2.3.2 with fix | @billing-team | Done |

### Short-term (This Sprint)

| Action | Owner | Due Date |
|--------|-------|----------|
| Add query performance CI check | @platform | Nov 15 |
| Create production-like staging data | @data-eng | Nov 20 |
| Add slow query alerting | @sre | Nov 12 |

### Long-term

| Action | Owner | Due Date |
|--------|-------|----------|
| Implement query analysis in PR reviews | @engineering | Q4 2024 |
| Automated performance regression tests | @qa | Q1 2025 |

## Lessons Learned

### What Went Well

- Fast detection (3 minutes from symptom to alert)
- Quick decision to rollback vs. hotfix
- No data loss or corruption
- Customer communication was proactive

### What Went Poorly

- Query wasn't tested with production-scale data
- No automated query plan analysis in CI
- Slow query monitoring threshold was too high (5s)

### Process Improvements

1. **Staging data:** Maintain production-scale dataset in staging
2. **Query review:** Add EXPLAIN ANALYZE to PR checklist
3. **Monitoring:** Lower slow query threshold to 1s
4. **Testing:** Require load tests for database-touching changes

## Technical Details

### Service Configuration

```yaml
service: billing-service
version: 2.3.1 (problematic)
database: PostgreSQL 14.9 (RDS)
connection_pool: 20 connections
timeout: 10 seconds
```

### Database Metrics During Incident

```
Active connections: 20/20 (saturated)
Lock wait time: 4.2s average
Slow queries/min: 340 (normal: 2)
CPU utilization: 95%
```

## Appendix

### Affected Customers

23 enterprise customers experienced failed transactions. All were contacted individually and transactions were successfully retried.

### References

- [Billing Service Architecture](/docs/services/billing)
- [Database Performance Guide](/docs/database/performance)
- [Incident Response Playbook](/docs/oncall/playbook)
