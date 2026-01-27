# On-Call Escalation Playbook

**Version:** 1.0.0
**Last Updated:** 2024-09-10
**Owner:** SRE Team
**Status:** Active
**Classification:** Restricted

## Overview

This playbook defines when and how to escalate incidents during on-call shifts. Following this decision tree ensures consistent incident response and appropriate stakeholder involvement.

## Severity Definitions

| Severity | Definition | Response Time | Escalation |
|----------|------------|---------------|------------|
| SEV-1 | Complete outage, all customers affected | 5 minutes | Immediate |
| SEV-2 | Major degradation, >10% customers affected | 15 minutes | 30 min if unresolved |
| SEV-3 | Minor issue, <10% customers affected | 1 hour | 2 hours if unresolved |
| SEV-4 | Low priority, no customer impact | Next business day | None |

## Escalation Decision Tree

```
Alert Received
      │
      ▼
┌─────────────────┐
│ Acknowledge     │
│ within 5 min    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Is this a SEV-1 (complete outage)?  │
└────────────────┬────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
       YES                NO
        │                 │
        ▼                 ▼
┌──────────────┐  ┌─────────────────────────────┐
│ IMMEDIATE    │  │ Can you diagnose and fix    │
│ ESCALATION   │  │ within 30 minutes?          │
│ to SRE Lead  │  └──────────────┬──────────────┘
└──────────────┘                 │
                        ┌────────┴────────┐
                        │                 │
                       YES                NO
                        │                 │
                        ▼                 ▼
                  ┌──────────┐     ┌──────────────┐
                  │ Continue │     │ ESCALATE to  │
                  │ working  │     │ next level   │
                  └──────────┘     └──────────────┘
```

## Escalation Contacts

### Primary Escalation Path

| Level | Role | Contact | When to Engage |
|-------|------|---------|----------------|
| L1 | On-Call SRE | PagerDuty rotation | First responder |
| L2 | SRE Lead | @jennifer.martinez | SEV-1, or SEV-2 > 30 min |
| L3 | VP Engineering | @david.kim | SEV-1 > 1 hour, customer escalation |
| L4 | CEO | @ceo | SEV-1 > 2 hours, PR required |

### Specialized Escalation

| System | Primary Contact | Backup |
|--------|-----------------|--------|
| Database | @database-oncall | @jennifer.martinez |
| Kafka | @kafka-oncall | @marcus.johnson |
| Kubernetes | @platform-oncall | @sarah.chen |
| Frontend | @frontend-oncall | @ui-team |
| Security | @security-oncall | @security-lead |

## Escalation Procedures

### SEV-1: Complete Outage

**Immediately:**
1. Acknowledge alert in PagerDuty
2. Post to #incidents: "SEV-1: [Brief description]"
3. Page SRE Lead
4. Start incident bridge (Zoom: cloudsignal.zoom.us/incident)

```bash
# Create incident channel
/incident create --severity=sev1 --description="[Description]"

# Page SRE Lead
pd trigger --service=sre-lead --message="SEV-1: [Description]"
```

**Within 15 minutes:**
- Identify affected services
- Implement mitigation (rollback, failover, scale)
- Update status page
- Draft customer communication

### SEV-2: Major Degradation

**Within 5 minutes:**
1. Acknowledge alert
2. Post to #incidents with initial assessment
3. Begin diagnosis

**Within 30 minutes (if unresolved):**
1. Escalate to SRE Lead
2. Request additional support if needed
3. Update #incidents with status

### SEV-3: Minor Issue

1. Acknowledge alert
2. Investigate during shift
3. Document findings
4. Escalate if cannot resolve within 2 hours

## Communication Templates

### Initial Incident Post

```
🚨 INCIDENT: [Brief Title]
Severity: SEV-[1/2/3]
Status: Investigating
Impact: [Description of customer impact]
Responder: @[your-name]
Next update: [time]
```

### Status Update

```
📊 UPDATE: [Incident Title]
Status: [Investigating/Identified/Monitoring/Resolved]
Current state: [What's happening now]
Actions taken: [What we've done]
Next steps: [What we're doing next]
ETA: [Expected resolution time]
```

### Resolution Post

```
✅ RESOLVED: [Incident Title]
Duration: [X hours Y minutes]
Root cause: [Brief description]
Resolution: [What fixed it]
Postmortem: [Link or "scheduled for DATE"]
```

## Status Page Updates

### When to Update

| Event | Status Page Action |
|-------|-------------------|
| SEV-1 started | Create incident immediately |
| SEV-2 started | Create incident within 15 min |
| Every 30 min during SEV-1 | Update status |
| Resolution | Mark resolved |

### Status Page CLI

```bash
# Create incident
statuspage incident create \
  --component="API" \
  --status="major_outage" \
  --message="Investigating API connectivity issues"

# Update incident
statuspage incident update \
  --id=<incident-id> \
  --status="identified" \
  --message="Root cause identified, implementing fix"

# Resolve incident
statuspage incident resolve \
  --id=<incident-id> \
  --message="Issue resolved, monitoring for stability"
```

## Customer Communication

### Criteria for Customer Communication

- SEV-1: Always communicate
- SEV-2 > 30 minutes: Communicate
- Enterprise customer impact: Always communicate
- Data integrity concern: Always communicate

### Communication Approval

| Severity | Approval Required |
|----------|------------------|
| SEV-1 | VP Engineering or above |
| SEV-2 | SRE Lead |
| SEV-3 | On-call engineer |

## Post-Incident

### Postmortem Required For

- All SEV-1 incidents
- SEV-2 incidents > 1 hour
- Any customer data impact
- Any security incident

### Postmortem Timeline

- Draft: Within 48 hours
- Review: Within 5 business days
- Action items assigned: Within 1 week

## On-Call Handoff

At end of shift:
1. Update #oncall-handoff with:
   - Active incidents
   - Ongoing investigations
   - Scheduled maintenance
2. Ensure PagerDuty rotation updated
3. Brief incoming on-call if active issues

## References

- [Incident Response Playbook](/docs/oncall/playbook)
- [Status Page Guide](/docs/statuspage)
- [Postmortem Template](/docs/templates/postmortem)
