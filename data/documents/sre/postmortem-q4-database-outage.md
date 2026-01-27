# Q4 2024 Database Outage Postmortem

**Incident ID:** INC-2024-1215
**Severity:** SEV-1 (Critical)
**Duration:** 3 hours 12 minutes
**Date:** December 15, 2024
**Author:** Jennifer Martinez, SRE Lead
**Status:** Active

## Executive Summary

On December 15, 2024, CloudSignal experienced a complete PostgreSQL database outage lasting 3 hours 12 minutes. The incident affected all customer-facing services, resulting in 100% unavailability of the dashboard, API, and alerting systems. Root cause was an undetected disk space exhaustion on the primary database node combined with a misconfigured failover mechanism.

## Impact

| Metric | Value |
|--------|-------|
| Duration | 3h 12m (10:23 AM - 1:35 PM EST) |
| Customers Affected | 100% (523 active customers) |
| Revenue Impact | ~$45,000 (SLA credits) |
| Alerts Delayed | ~15,000 alerts |
| Data Loss | None (full recovery) |

### Services Affected

- **Dashboard:** Complete outage
- **REST API:** 100% error rate
- **Metrics Ingestion:** Buffered in Kafka (no loss)
- **Alerting:** Delayed by 3+ hours

## Timeline (All times EST)

| Time | Event |
|------|-------|
| 10:15 AM | WAL archive disk reaches 95% capacity |
| 10:18 AM | PostgreSQL primary begins rejecting writes |
| 10:23 AM | First customer reports dashboard errors |
| 10:25 AM | PagerDuty alert: "Database connection pool exhausted" |
| 10:28 AM | On-call SRE (Marcus) acknowledges, begins investigation |
| 10:35 AM | Identified: Primary DB not accepting connections |
| 10:42 AM | Attempted failover to replica - FAILED |
| 10:45 AM | Escalation to SRE Lead and VP Engineering |
| 11:00 AM | Root cause identified: WAL disk full |
| 11:15 AM | Emergency disk expansion initiated |
| 11:45 AM | Disk expansion complete, PostgreSQL restart attempted |
| 12:00 PM | Database online but replica sync broken |
| 12:30 PM | Manual replica resync initiated |
| 1:15 PM | Replica sync complete, failover tested |
| 1:35 PM | Full service restoration confirmed |
| 2:00 PM | Incident closed, monitoring period begins |

## Root Cause Analysis

### Primary Cause: Disk Space Exhaustion

The PostgreSQL WAL (Write-Ahead Log) archive disk filled to 100% capacity due to:

1. **Increased write volume:** Black Friday traffic increased WAL generation by 3x
2. **Archive retention misconfiguration:** Retention policy was set to 30 days instead of 7
3. **Monitoring gap:** Disk space alerts were set at 90%, but disk filled from 85% to 100% in 4 hours

### Secondary Cause: Failover Failure

The automatic failover to the replica failed because:

1. **Replica was 2 hours behind:** Replication lag had grown unnoticed
2. **Patroni misconfiguration:** Failover threshold was set too high (5 minutes)
3. **No recent failover test:** Last DR test was 6 months ago

## Contributing Factors

1. **Monitoring blindspot:** No alert for WAL disk specifically
2. **Runbook outdated:** Failover runbook referenced deprecated tools
3. **Knowledge gap:** On-call engineer unfamiliar with Patroni
4. **Weekend timing:** Reduced staffing slowed response

## Action Items

### Immediate (Completed)

| Action | Owner | Status |
|--------|-------|--------|
| Reduce WAL retention to 7 days | @marcus | Done |
| Add WAL disk-specific alert | @jennifer | Done |
| Update Patroni failover config | @sarah | Done |
| Run emergency DR test | @sre-team | Done |

### Short-term (This Sprint)

| Action | Owner | Due Date |
|--------|-------|----------|
| Add replication lag alerting | @marcus | Dec 22 |
| Update failover runbook | @jennifer | Dec 22 |
| Cross-train team on Patroni | @sarah | Dec 29 |
| Implement automated DR testing | @platform-team | Jan 5 |

### Long-term (Next Quarter)

| Action | Owner | Due Date |
|--------|-------|----------|
| Migrate to managed RDS | @infrastructure | Q1 2025 |
| Implement chaos engineering | @sre-team | Q1 2025 |
| Review all disk space alerts | @monitoring | Jan 15 |

## Lessons Learned

### What Went Well

- Kafka buffering prevented metric data loss
- Customer communication was timely and clear
- Team collaboration during incident was excellent
- Full recovery with no data loss

### What Went Poorly

- Failover mechanism was untested and broken
- Initial diagnosis took too long (17 minutes)
- Runbooks were outdated
- Single point of failure on WAL disk

### Where We Got Lucky

- Incident occurred during business hours (faster response)
- No customer data was lost
- Kafka retention held all buffered metrics

## Technical Details

### Database Configuration

```
PostgreSQL Version: 14.9
Instance Type: r6g.2xlarge
Storage: 500GB gp3 (main), 200GB gp3 (WAL)
Replication: Streaming async to 1 replica
HA: Patroni with etcd
```

### Disk Usage at Incident

```
/var/lib/postgresql/data:     78% used (390GB/500GB)
/var/lib/postgresql/wal:     100% used (200GB/200GB)  <-- PROBLEM
```

### Failover Attempt Logs

```
2024-12-15 10:42:15 ERROR: Patroni failover failed
  Reason: Replica lag exceeds maximum_lag_on_failover (300s)
  Current lag: 7234 seconds
  Action: Manual intervention required
```

## Appendix

### Related Incidents

- INC-2024-0601: API Gateway latency (unrelated)
- INC-2024-0312: Replica sync issue (similar root cause)

### References

- [Database Failover Runbook](/docs/runbooks/database-failover)
- [Patroni Configuration Guide](/docs/infrastructure/patroni)
- [Incident Response Playbook](/docs/oncall/playbook)
