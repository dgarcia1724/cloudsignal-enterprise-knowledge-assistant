# Database Failover Runbook

**Version:** 2.1.0
**Last Updated:** 2024-12-15
**Owner:** SRE Team
**Status:** Active
**Classification:** Restricted

## Overview

This runbook describes the procedure for failing over the CloudSignal PostgreSQL database from primary to replica. Use this during planned maintenance or unplanned outages.

**CRITICAL:** This runbook is restricted to SRE team members only. Unauthorized execution may cause data loss.

## Prerequisites

- SRE team member or above
- VPN connected to production network
- Access to `sre-admin` Kubernetes namespace
- Patroni CLI installed and configured
- PagerDuty incident created

## Decision Tree

```
Database Issue Detected
         │
         ▼
┌────────────────────┐
│ Is primary         │
│ responding?        │
└────────┬───────────┘
         │
    ┌────┴────┐
    │         │
   YES        NO
    │         │
    ▼         ▼
┌────────┐ ┌────────────────┐
│Diagnose│ │Check replica   │
│primary │ │status          │
└────────┘ └───────┬────────┘
                   │
              ┌────┴────┐
              │         │
           HEALTHY   UNHEALTHY
              │         │
              ▼         ▼
         ┌────────┐ ┌────────────┐
         │FAILOVER│ │RESTORE FROM│
         │        │ │BACKUP      │
         └────────┘ └────────────┘
```

## Procedure

### Step 1: Assess Current State

```bash
# Check Patroni cluster status
patronictl -c /etc/patroni/patroni.yml list

# Expected output:
# + Cluster: cloudsignal-prod (123456789) ----+
# | Member    | Host        | Role    | State   | TL | Lag in MB |
# +-----------+-------------+---------+---------+----+-----------+
# | postgres-0| 10.0.1.100  | Leader  | running |  5 |           |
# | postgres-1| 10.0.1.101  | Replica | running |  5 |       0.0 |
# +-----------+-------------+---------+---------+----+-----------+
```

**Check for:**
- Replica is in `running` state
- Lag is less than 100MB
- Timeline (TL) matches between nodes

### Step 2: Verify Replica Health

```bash
# Connect to replica and check replication
psql -h postgres-1.cloudsignal-db -U postgres -c "
SELECT
  pg_is_in_recovery() as is_replica,
  pg_last_wal_receive_lsn() as received,
  pg_last_wal_replay_lsn() as replayed,
  pg_last_wal_receive_lsn() - pg_last_wal_replay_lsn() as lag_bytes
;"
```

**Proceed only if:**
- `is_replica` = true
- `lag_bytes` < 10MB (for planned failover)
- `lag_bytes` < 100MB (for emergency failover)

### Step 3: Notify Stakeholders

```bash
# Post to #incidents Slack channel
/incident update \
  --status="Initiating database failover" \
  --action="Expect 30-60 second connection interruption"
```

### Step 4: Execute Failover

#### Option A: Planned Failover (Preferred)

```bash
# Graceful switchover with Patroni
patronictl -c /etc/patroni/patroni.yml switchover \
  --master postgres-0 \
  --candidate postgres-1 \
  --scheduled now

# Confirm switchover
# Type 'postgres-0' when prompted for current leader
# Type 'postgres-1' when prompted for candidate
# Type 'now' when prompted for scheduled time
```

#### Option B: Emergency Failover

```bash
# Force failover (use when primary is unresponsive)
patronictl -c /etc/patroni/patroni.yml failover \
  --candidate postgres-1 \
  --force
```

**WARNING:** Emergency failover may result in data loss for uncommitted transactions.

### Step 5: Verify Failover Success

```bash
# Check new cluster state
patronictl -c /etc/patroni/patroni.yml list

# Verify new leader
psql -h postgres-read.cloudsignal-db -U postgres -c "
SELECT pg_is_in_recovery();
"
# Should return 'false' for the new primary

# Test write capability
psql -h postgres-write.cloudsignal-db -U postgres -c "
SELECT NOW();
INSERT INTO health_check (checked_at) VALUES (NOW());
"
```

### Step 6: Validate Application Connectivity

```bash
# Check application database connections
kubectl exec -it deploy/api-server -- \
  curl -s localhost:8080/health/database

# Check connection pool status
kubectl exec -it deploy/api-server -- \
  curl -s localhost:8080/metrics | grep db_pool
```

### Step 7: Restore Replica

After failover, the old primary needs to be rebuilt as replica:

```bash
# Reinitialize old primary as replica
patronictl -c /etc/patroni/patroni.yml reinit postgres-0

# Monitor reinitialization
watch "patronictl -c /etc/patroni/patroni.yml list"
```

## Rollback Procedure

If failover causes issues, failover again to the original primary:

```bash
# Only if original primary is healthy
patronictl -c /etc/patroni/patroni.yml switchover \
  --master postgres-1 \
  --candidate postgres-0 \
  --scheduled now
```

## Troubleshooting

### Failover Fails: "No suitable candidate"

```bash
# Check replica lag
patronictl -c /etc/patroni/patroni.yml list

# If lag is too high, wait or force:
patronictl -c /etc/patroni/patroni.yml failover --force
```

### Applications Not Reconnecting

```bash
# Restart connection pools
kubectl rollout restart deploy/api-server
kubectl rollout restart deploy/metrics-service
```

### Split Brain Detected

**CRITICAL:** Immediately fence one node:

```bash
# Stop Patroni on one node
kubectl exec postgres-0 -- patronictl pause
kubectl exec postgres-0 -- pg_ctl stop -D /var/lib/postgresql/data
```

## Post-Failover Checklist

- [ ] New primary accepting writes
- [ ] Replica resync initiated
- [ ] Application connectivity verified
- [ ] Monitoring alerts cleared
- [ ] Incident updated in PagerDuty
- [ ] Stakeholders notified of completion

## Emergency Contacts

| Role | Contact |
|------|---------|
| SRE Lead | @jennifer.martinez |
| Database DBA | @database-oncall |
| VP Engineering | @david.kim (escalation) |

## References

- [Patroni Documentation](https://patroni.readthedocs.io/)
- [PostgreSQL Failover Guide](/docs/database/failover)
- [Incident Response Playbook](/docs/oncall/playbook)
