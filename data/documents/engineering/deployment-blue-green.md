# Blue-Green Deployment Procedure

**Version:** 1.0.0
**Last Updated:** 2024-09-25
**Owner:** Platform Team
**Status:** Active

## Overview

Blue-green deployment is our strategy for zero-downtime releases of critical services. This document describes the procedure for executing blue-green deployments at CloudSignal.

## Concept

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
        ┌─────▼─────┐                 ┌─────▼─────┐
        │   BLUE    │                 │   GREEN   │
        │  (Live)   │                 │  (Idle)   │
        │  v1.2.3   │                 │  v1.2.4   │
        └───────────┘                 └───────────┘
```

## When to Use Blue-Green

**Use Blue-Green for:**
- Database schema changes
- Major version upgrades
- Services with long startup times
- Changes requiring instant rollback

**Use Rolling Deployment for:**
- Minor bug fixes
- Configuration changes
- Stateless service updates

## Procedure

### Phase 1: Prepare Green Environment

1. **Create Green Deployment**

```bash
# Create green deployment with new version
kubectl apply -f deployment-green.yaml

# Verify pods are running
kubectl get pods -l deployment=green -n production
```

2. **Run Health Checks**

```bash
# Wait for all pods to be ready
kubectl wait --for=condition=ready pod \
  -l deployment=green -n production \
  --timeout=300s

# Verify internal health endpoints
for pod in $(kubectl get pods -l deployment=green -o name); do
  kubectl exec $pod -- curl -s localhost:8080/health
done
```

3. **Run Smoke Tests Against Green**

```bash
# Port-forward to green service
kubectl port-forward svc/service-green 8081:80 &

# Run smoke tests
cs-test smoke --target=localhost:8081
```

### Phase 2: Traffic Switch

4. **Switch Traffic to Green**

```bash
# Update service selector to point to green
kubectl patch svc main-service -n production \
  -p '{"spec":{"selector":{"deployment":"green"}}}'

# Verify traffic is flowing to green
kubectl logs -l deployment=green -n production --tail=10
```

5. **Monitor for Issues**

Watch these metrics for 10 minutes:
- Error rate (Grafana: CloudSignal > Service Health)
- Latency p50, p99
- Request throughput

```bash
# Quick check via CLI
cs-metrics query \
  --metric=http.error_rate \
  --service=<service-name> \
  --duration=10m
```

### Phase 3: Cleanup

6. **If Successful: Remove Blue**

```bash
# Scale down blue deployment
kubectl scale deployment blue-deployment --replicas=0

# After 1 hour, delete blue resources
kubectl delete deployment blue-deployment
```

7. **Rename Green to Blue**

```bash
# For next deployment, green becomes the new blue
kubectl label deployment green-deployment deployment=blue --overwrite
```

## Rollback Procedure

If issues are detected, immediately rollback:

```bash
# Switch traffic back to blue
kubectl patch svc main-service -n production \
  -p '{"spec":{"selector":{"deployment":"blue"}}}'

# Verify traffic is on blue
kubectl logs -l deployment=blue -n production --tail=10

# Scale down failed green
kubectl scale deployment green-deployment --replicas=0
```

**Rollback SLA:** Complete within 2 minutes of issue detection.

## Database Considerations

For deployments with database changes:

1. **Schema changes must be backward compatible**
2. **Use expand-contract pattern:**
   - Deploy: Add new columns/tables
   - Migrate: Backfill data
   - Cleanup: Remove old columns (next release)

3. **Run migrations before traffic switch:**

```bash
# Apply migrations against production DB
cs-migrate run --environment=production

# Verify migration success
cs-migrate status --environment=production
```

## Checklist

### Pre-Deployment
- [ ] Green environment provisioned
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Database migrations applied
- [ ] Rollback plan reviewed

### During Deployment
- [ ] Traffic switched to green
- [ ] Metrics monitored for 10 minutes
- [ ] No error rate increase
- [ ] No latency regression

### Post-Deployment
- [ ] Blue environment scaled down
- [ ] Deployment logged in Jira
- [ ] Team notified of completion

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Green pods not starting | Check resource limits, image pull |
| Health checks failing | Verify dependencies, DB connection |
| High error rate after switch | Immediate rollback to blue |
| Slow traffic drain from blue | Check connection keep-alive settings |
