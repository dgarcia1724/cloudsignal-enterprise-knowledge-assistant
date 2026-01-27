# Legacy Bare Metal Deployment Procedure

**Version:** 1.0.0
**Last Updated:** 2024-01-15
**Owner:** SRE Team
**Status:** DEPRECATED

---

## ⚠️ DEPRECATION NOTICE

**This document is deprecated as of January 2024.**

CloudSignal has fully migrated to Kubernetes. This runbook is retained for historical reference only.

**For current deployment procedures, see:**
- [Production Deployment Checklist](/docs/deployment/production-checklist)
- [Blue-Green Deployment Procedure](/docs/deployment/blue-green)

---

## Historical Context

Prior to 2024, CloudSignal ran on bare metal servers in two data centers. This document described the deployment process for that infrastructure.

## Legacy Architecture (Pre-2024)

```
┌─────────────────────────────────────────────┐
│              Data Center 1 (Primary)         │
├─────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ web-01  │  │ web-02  │  │ web-03  │     │
│  └────┬────┘  └────┬────┘  └────┬────┘     │
│       └──────────┬─┴───────────┘           │
│                  │                          │
│  ┌─────────┐  ┌──┴──────┐  ┌─────────┐    │
│  │ api-01  │  │   HAProxy│  │ api-02  │    │
│  └─────────┘  └─────────┘  └─────────┘    │
│                                             │
│  ┌─────────┐  ┌─────────┐                  │
│  │ db-01   │  │ db-02   │                  │
│  │(primary)│  │(replica)│                  │
│  └─────────┘  └─────────┘                  │
└─────────────────────────────────────────────┘
```

## Legacy Deployment Steps

### Prerequisites (Historical)

- SSH access to all servers
- Ansible playbooks from `deploy/ansible/`
- Release artifacts in S3

### Step 1: Build Release

```bash
# Build application
./build.sh --version=$VERSION

# Upload to S3
aws s3 cp dist/cloudsignal-$VERSION.tar.gz s3://releases/
```

### Step 2: Deploy to Staging

```bash
# Run Ansible playbook
ansible-playbook -i inventory/staging deploy.yml \
  -e version=$VERSION
```

### Step 3: Deploy to Production

```bash
# Deploy web tier (rolling)
ansible-playbook -i inventory/production deploy-web.yml \
  -e version=$VERSION \
  --limit=web-01

# Verify web-01
curl http://web-01.internal/health

# Continue with web-02, web-03
ansible-playbook -i inventory/production deploy-web.yml \
  -e version=$VERSION \
  --limit=web-02,web-03

# Deploy API tier
ansible-playbook -i inventory/production deploy-api.yml \
  -e version=$VERSION
```

### Step 4: Database Migrations

```bash
# SSH to db-01
ssh db-01.internal

# Run migrations
cd /opt/cloudsignal
./manage.py migrate --settings=production
```

## Why We Migrated to Kubernetes

1. **Manual scaling:** Adding capacity required weeks of hardware provisioning
2. **Deployment risk:** No easy rollback, deployments took 2+ hours
3. **Inconsistency:** Configuration drift between servers
4. **Cost:** Maintaining two data centers was expensive
5. **Disaster recovery:** Failover was manual and error-prone

## Migration Timeline

| Date | Milestone |
|------|-----------|
| Q2 2023 | Kubernetes cluster provisioned |
| Q3 2023 | Stateless services migrated |
| Q4 2023 | Database migrated to RDS |
| Q1 2024 | Bare metal decommissioned |

## References

- [Microservices Migration RFC](/docs/rfc/microservices-migration)
- [Kubernetes Deployment Guide](/docs/deployment/kubernetes)

---

*This document is preserved for audit and historical purposes only.*
