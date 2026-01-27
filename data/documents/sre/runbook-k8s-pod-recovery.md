# Kubernetes Pod Recovery Procedure

**Version:** 1.3.0
**Last Updated:** 2024-10-05
**Owner:** Platform SRE Team
**Status:** Active
**Classification:** Restricted

## Overview

This runbook provides procedures for diagnosing and recovering failed Kubernetes pods in CloudSignal's production environment.

## Quick Reference

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| CrashLoopBackOff | App crash, config error | Check logs, rollback |
| ImagePullBackOff | Registry issue, wrong tag | Verify image, check secrets |
| Pending | Resource constraints | Scale cluster, check quotas |
| OOMKilled | Memory exceeded | Increase limits, fix leak |
| Evicted | Node pressure | Rebalance, check disk |

## Diagnostic Commands

### Check Pod Status

```bash
# List pods with issues
kubectl get pods -n production --field-selector=status.phase!=Running

# Get detailed pod info
kubectl describe pod <pod-name> -n production

# Check recent events
kubectl get events -n production --sort-by='.lastTimestamp' | tail -20
```

### Check Logs

```bash
# Current container logs
kubectl logs <pod-name> -n production

# Previous container logs (after crash)
kubectl logs <pod-name> -n production --previous

# All containers in pod
kubectl logs <pod-name> -n production --all-containers

# Stream logs
kubectl logs -f <pod-name> -n production
```

## Recovery Procedures

### CrashLoopBackOff

**Symptoms:** Pod repeatedly starts and crashes

**Diagnosis:**
```bash
# Check crash reason
kubectl describe pod <pod-name> -n production | grep -A 5 "Last State"

# Check logs from crashed container
kubectl logs <pod-name> -n production --previous
```

**Common Causes & Fixes:**

1. **Application Error**
   ```bash
   # Check for stack traces in logs
   kubectl logs <pod-name> --previous | grep -i "error\|exception"

   # Rollback if recent deployment
   kubectl rollout undo deployment/<deployment-name> -n production
   ```

2. **Configuration Error**
   ```bash
   # Check ConfigMap/Secret values
   kubectl get configmap <name> -n production -o yaml
   kubectl get secret <name> -n production -o yaml
   ```

3. **Health Check Failure**
   ```bash
   # Check probe configuration
   kubectl get deployment <name> -n production -o yaml | grep -A 10 "livenessProbe"

   # Temporarily disable for debugging
   kubectl patch deployment <name> -n production --type=json \
     -p='[{"op": "remove", "path": "/spec/template/spec/containers/0/livenessProbe"}]'
   ```

### ImagePullBackOff

**Symptoms:** Pod cannot pull container image

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n production | grep -A 3 "Events"
```

**Fixes:**

1. **Wrong Image Tag**
   ```bash
   # Check current image
   kubectl get deployment <name> -n production -o jsonpath='{.spec.template.spec.containers[0].image}'

   # Fix image tag
   kubectl set image deployment/<name> <container>=<correct-image>
   ```

2. **Registry Authentication**
   ```bash
   # Check image pull secrets
   kubectl get deployment <name> -n production -o jsonpath='{.spec.template.spec.imagePullSecrets}'

   # Verify secret exists
   kubectl get secret regcred -n production
   ```

### OOMKilled

**Symptoms:** Container killed due to memory limit

**Diagnosis:**
```bash
# Check memory usage before kill
kubectl describe pod <pod-name> -n production | grep -A 5 "Last State"

# Check current limits
kubectl get deployment <name> -n production -o jsonpath='{.spec.template.spec.containers[0].resources}'
```

**Fixes:**

1. **Increase Memory Limit**
   ```bash
   kubectl patch deployment <name> -n production --type=json \
     -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "2Gi"}]'
   ```

2. **Investigate Memory Leak**
   ```bash
   # Get heap dump (Java)
   kubectl exec <pod-name> -- jmap -dump:format=b,file=/tmp/heap.hprof 1
   kubectl cp <pod-name>:/tmp/heap.hprof ./heap.hprof
   ```

### Pod Stuck in Pending

**Symptoms:** Pod not scheduled to any node

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n production | grep -A 10 "Events"
```

**Fixes:**

1. **Insufficient Resources**
   ```bash
   # Check node capacity
   kubectl describe nodes | grep -A 5 "Allocated resources"

   # Scale cluster (if using autoscaler)
   kubectl scale deployment <name> --replicas=<current-1>
   ```

2. **Node Selector/Affinity**
   ```bash
   # Check node selector
   kubectl get deployment <name> -n production -o jsonpath='{.spec.template.spec.nodeSelector}'

   # Check available nodes with label
   kubectl get nodes -l <label>=<value>
   ```

### Pod Evicted

**Symptoms:** Pod evicted due to node pressure

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n production | grep "Evicted"
kubectl describe node <node-name> | grep -A 10 "Conditions"
```

**Fixes:**

```bash
# Clean up evicted pods
kubectl delete pods --field-selector=status.phase==Failed -n production

# Check disk pressure
kubectl describe node <node-name> | grep "DiskPressure"

# Drain and repair node if needed
kubectl drain <node-name> --ignore-daemonsets
```

## Service Recovery

### Full Deployment Restart

```bash
# Rolling restart
kubectl rollout restart deployment/<name> -n production

# Monitor rollout
kubectl rollout status deployment/<name> -n production
```

### Rollback Deployment

```bash
# Check rollout history
kubectl rollout history deployment/<name> -n production

# Rollback to previous
kubectl rollout undo deployment/<name> -n production

# Rollback to specific revision
kubectl rollout undo deployment/<name> --to-revision=<n> -n production
```

## Post-Recovery Checklist

- [ ] Pods running and healthy
- [ ] Service endpoints updated
- [ ] Application responding to health checks
- [ ] Metrics flowing normally
- [ ] Alerts cleared
- [ ] Incident documented

## Escalation

If unable to recover within 15 minutes:

1. Page SRE Lead: `pd trigger --service=sre-escalation`
2. Post update to #incidents
3. Consider customer communication if user-facing

## References

- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug/)
- [CloudSignal Deployment Guide](/docs/deployment)
- [On-Call Escalation Playbook](/docs/oncall/escalation)
