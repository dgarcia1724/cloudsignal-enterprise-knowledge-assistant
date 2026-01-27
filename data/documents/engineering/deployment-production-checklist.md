# Production Deployment Checklist

**Version:** 3.2.0
**Last Updated:** 2025-01-15
**Owner:** Platform Team
**Status:** Active

## Overview

This checklist must be completed for all production deployments. Skipping steps requires VP Engineering approval.

## Pre-Deployment Checklist

### Code Quality

- [ ] All CI checks passing (unit tests, integration tests, linting)
- [ ] Code reviewed and approved by at least 2 engineers
- [ ] No critical or high-severity security vulnerabilities
- [ ] Test coverage meets minimum threshold (80%)
- [ ] Documentation updated for any API changes

### Change Management

- [ ] Change request ticket created in Jira
- [ ] Deployment window scheduled (avoid peak hours: 9am-11am, 2pm-4pm EST)
- [ ] Rollback plan documented
- [ ] On-call engineer notified
- [ ] Customer communication prepared (if user-facing changes)

### Environment Validation

- [ ] Staging deployment successful
- [ ] Staging smoke tests passing
- [ ] No performance regression in staging
- [ ] Database migrations tested in staging
- [ ] Feature flags configured correctly

## Deployment Steps

### Step 1: Notify Team

```bash
# Post to #deployments Slack channel
/cloudsignal deploy notify \
  --service=<service-name> \
  --version=<version> \
  --engineer=<your-name>
```

### Step 2: Create Deployment

```bash
# Trigger deployment via CLI
cs-deploy create \
  --service=<service-name> \
  --version=<version> \
  --strategy=rolling \
  --max-unavailable=25%
```

### Step 3: Monitor Rollout

Watch deployment progress:

```bash
kubectl rollout status deployment/<service-name> -n production
```

Monitor key metrics:
- Error rate (should not increase >0.1%)
- Latency p99 (should not increase >10%)
- CPU/Memory usage

### Step 4: Verify Health

```bash
# Run health checks
cs-deploy verify --service=<service-name>

# Check endpoints
curl https://api.cloudsignal.io/health
curl https://api.cloudsignal.io/ready
```

### Step 5: Run Smoke Tests

```bash
# Execute production smoke tests
cs-test smoke --environment=production
```

## Post-Deployment Checklist

- [ ] All pods healthy and running
- [ ] No increase in error rates
- [ ] Latency within acceptable range
- [ ] Smoke tests passing
- [ ] Deployment marked successful in Jira
- [ ] #deployments channel updated with completion status

## Rollback Procedure

If issues are detected:

### Automatic Rollback

Deployments automatically rollback if:
- Health checks fail for >3 minutes
- Error rate exceeds 5%
- P99 latency exceeds 10s

### Manual Rollback

```bash
# Rollback to previous version
cs-deploy rollback --service=<service-name>

# Or rollback to specific version
cs-deploy rollback --service=<service-name> --version=<previous-version>
```

## Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call SRE | PagerDuty | Auto-page |
| Platform Lead | @sarah-chen | Slack/Phone |
| VP Engineering | @david-kim | Phone only |

## Deployment Windows

| Day | Preferred | Avoid |
|-----|-----------|-------|
| Monday | 2pm-5pm EST | Before noon |
| Tuesday-Thursday | 10am-5pm EST | Peak hours |
| Friday | 10am-2pm EST | After 2pm |
| Weekend | Emergency only | All |

## Appendix

### Service-Specific Notes

**metrics-service:**
- Requires Kafka connection validation
- Scale up consumers before high-traffic deployments

**alerting-service:**
- Verify Flink checkpoint before deployment
- Pause alert delivery during rollout if needed

**dashboard-service:**
- Clear CDN cache after deployment
- Verify WebSocket connections
