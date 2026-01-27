# API Gateway Latency Incident - June 2024

**Incident ID:** INC-2024-0615
**Severity:** SEV-2 (Major)
**Duration:** 1 hour 23 minutes
**Date:** June 15, 2024
**Author:** Marcus Johnson, SRE
**Status:** DEPRECATED

---

## ⚠️ DEPRECATION NOTICE

**This postmortem has been superseded.**

The root cause identified in this incident was later found to be a symptom of a larger architectural issue, which is fully analyzed in:

**[Q4 2024 Database Outage Postmortem](/docs/postmortems/q4-database-outage)**

This document is retained for historical reference.

---

## Executive Summary

On June 15, 2024, CloudSignal's API Gateway experienced latency spikes causing p99 response times to increase from 150ms to 4.5 seconds. The incident affected all API endpoints for 1 hour 23 minutes.

## Impact

| Metric | Value |
|--------|-------|
| Duration | 1h 23m (3:45 PM - 5:08 PM EST) |
| Customers Affected | ~40% |
| API Error Rate | 12% (vs 0.1% baseline) |
| Dashboard Load Time | 8s (vs 2s baseline) |

## Timeline

| Time | Event |
|------|-------|
| 3:45 PM | Alert: API Gateway p99 latency > 1s |
| 3:48 PM | On-call acknowledges, begins investigation |
| 3:55 PM | Identified: Connection pool exhaustion |
| 4:10 PM | Increased connection pool size |
| 4:15 PM | Latency improved but still elevated |
| 4:30 PM | Discovered: Database replica lag |
| 4:45 PM | Directed read traffic to primary |
| 5:00 PM | Latency normalized |
| 5:08 PM | Incident resolved |

## Root Cause (Original Analysis)

*Note: This analysis was later found to be incomplete. See superseding document.*

The original analysis identified:

1. **Connection pool exhaustion:** API Gateway connection pool was undersized for traffic
2. **Database replica lag:** Read replica fell 30 seconds behind

## Action Items (Completed)

| Action | Owner | Status |
|--------|-------|--------|
| Increase connection pool | @marcus | Done |
| Add replica lag alerting | @jennifer | Done |
| Review database topology | @database-team | Done |

## Later Findings

This incident was a precursor to the more severe Q4 2024 database outage. The common root causes identified later:

1. **WAL disk sizing:** Insufficient for traffic growth
2. **Patroni configuration:** Failover settings too conservative
3. **Monitoring gaps:** Missing disk-specific alerts

All comprehensive action items are tracked in the Q4 2024 postmortem.

---

## References

- [Q4 2024 Database Outage Postmortem](/docs/postmortems/q4-database-outage) ← **Current document**
- [Database Failover Runbook](/docs/runbooks/database-failover)

---

*This postmortem is preserved for audit and historical reference.*
