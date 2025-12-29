# CloudSignal Role Personas & Access Patterns

This document defines the six primary user roles in the CloudSignal knowledge assistant system, their responsibilities, access patterns, and typical information needs.

---

## Table of Contents

1. [Role Overview](#role-overview)
2. [Detailed Role Personas](#detailed-role-personas)
   - [Engineer](#1-engineer)
   - [Site Reliability Engineer (SRE)](#2-site-reliability-engineer-sre)
   - [Product Manager](#3-product-manager)
   - [HR Specialist](#4-hr-specialist)
   - [Manager](#5-manager)
   - [Administrator](#6-administrator)
3. [Cross-Role Scenarios](#cross-role-scenarios)
4. [Access Level Hierarchy](#access-level-hierarchy)

---

## Role Overview

| Role | Count | Primary Department | Access Scope | Key Permissions |
|------|-------|-------------------|--------------|-----------------|
| Engineer | ~100 | Engineering | Engineering + SRE docs | Technical documentation, postmortems |
| SRE | ~30 | SRE | SRE + Engineering docs | Incident runbooks, security incidents, deprecated docs |
| Product Manager | ~20 | Product | Product docs | Roadmaps, specs, customer feedback |
| HR Specialist | ~20 | HR | HR docs | Policies, salary bands, performance reviews |
| Manager | ~50 | All departments | Department-specific + team docs | Performance reviews (reports), budgets |
| Administrator | ~10 | Leadership, HR, IT | All documents | Full system access, audit logs |

---

## Detailed Role Personas

### 1. Engineer

**Fictional Persona**: Alex Chen, Senior Backend Engineer

**Background**:
- 5 years of experience in distributed systems
- Works on the Backend Platform team
- On-call rotation for the API service
- Mentors junior engineers

**Daily Responsibilities**:
- Design and implement new API features
- Review code from teammates
- Debug production issues during on-call
- Write technical design documents
- Participate in architecture review meetings
- Contribute to engineering documentation

**Information Needs**:
- **Deployment procedures**: "How do I deploy to staging/production?"
- **API standards**: "What is our API versioning strategy?"
- **Incident postmortems**: "What caused the database outage last month?"
- **Code conventions**: "What are our Python coding standards?"
- **Onboarding docs**: "How do I set up my local development environment?"
- **Architecture diagrams**: "How does authentication work in our system?"

**Access Patterns**:
- ✅ **Can access**: Engineering docs (internal), SRE runbooks (internal), public onboarding docs
- ❌ **Cannot access**: HR docs, salary information, leadership financials, product roadmaps (restricted), security incidents (confidential)
- ⚠️ **Special cases**:
  - Can access postmortems for incidents they were involved in
  - Cannot access deprecated docs (prefer current versions)
  - Can view design docs from other engineering teams (internal level)

**Typical Queries**:
```
- "How do I roll back a deployment?"
- "What is the incident response procedure for P1 alerts?"
- "What were the lessons learned from the Q4 database outage?"
- "How do I configure authentication for our microservices?"
- "What is our strategy for migrating to Kubernetes?"
```

**Security Considerations**:
- Engineers should NOT access salary bands, performance reviews, or financial data
- Should NOT see security incident details (handled by SRE + Security team)
- Access to customer data requires explicit approval (not in scope for this system)

---

### 2. Site Reliability Engineer (SRE)

**Fictional Persona**: Jordan Martinez, Senior SRE

**Background**:
- 7 years in SRE/DevOps roles
- 24/7 on-call rotation (primary/secondary)
- Expertise in Kubernetes, PostgreSQL, incident response
- Maintains critical runbooks

**Daily Responsibilities**:
- Respond to production incidents (P0/P1)
- Maintain 99.99% uptime SLA
- Manage Kubernetes clusters and databases
- Write and update incident runbooks
- Conduct postmortem reviews
- Develop automation tools
- Mentor junior SREs and on-call engineers

**Information Needs**:
- **Incident runbooks**: "What is the runbook for database failover?"
- **Architecture docs**: "How is our service mesh configured?"
- **Security incidents**: "What steps do we take for a DDoS attack?"
- **Postmortems**: "What were the root causes of recent P0 incidents?"
- **Deprecated runbooks**: "How did we handle incidents before the Kubernetes migration?"
- **Engineering design docs**: "What dependencies does the API service have?"

**Access Patterns**:
- ✅ **Can access**: SRE docs (all levels), engineering docs (internal), security incidents (confidential), deprecated runbooks
- ❌ **Cannot access**: HR salary data, leadership financial projections, product roadmaps (unless public)
- ⚠️ **Special cases**:
  - **Full access to deprecated docs** (need historical context for incident response)
  - Can access security incidents (SRE often responds to security events)
  - Can view engineering design docs (need to understand system architecture)

**Typical Queries**:
```
- "What is the disaster recovery procedure for PostgreSQL?"
- "How do I escalate a P0 incident to leadership?"
- "What are the monitoring thresholds for API latency?"
- "How do we handle a complete AWS region failure?"
- "What was the runbook we used before we migrated to Kubernetes?" (deprecated)
```

**Security Considerations**:
- SREs have elevated access due to incident response needs
- Should NOT access HR/financial data (not relevant to their role)
- Access to security incidents is CRITICAL for their job function
- Deprecated docs access is NECESSARY (historical incident context)

---

### 3. Product Manager

**Fictional Persona**: Sarah Thompson, Senior Product Manager

**Background**:
- 6 years in product management at SaaS companies
- Owns the alerting and dashboards product area
- Conducts user research and customer interviews
- Collaborates closely with engineering and design

**Daily Responsibilities**:
- Define product roadmap and prioritize features
- Gather customer feedback and requirements
- Write product requirement documents (PRDs)
- Conduct competitive analysis
- Track product metrics (adoption, engagement)
- Align with leadership on product strategy
- Collaborate with engineering on technical feasibility

**Information Needs**:
- **Product roadmaps**: "What is our Q1 2025 roadmap?"
- **Customer feedback**: "What features are customers requesting most?"
- **Feature specs**: "What is the scope of the new dashboard redesign?"
- **Competitive analysis**: "How does our alerting compare to Datadog?"
- **Product metrics**: "What is the adoption rate for the mobile app?"
- **Engineering context**: "What are the technical constraints for real-time dashboards?"

**Access Patterns**:
- ✅ **Can access**: Product docs (all levels), public engineering docs, customer feedback, competitive analysis
- ❌ **Cannot access**: Engineering internal docs (except when granted), SRE runbooks, HR data, detailed financial projections
- ⚠️ **Special cases**:
  - May be granted temporary access to engineering design docs for specific features
  - Can access high-level engineering architecture docs (if marked as product-relevant)
  - Cannot access deprecated product roadmaps by default (prefer current versions)

**Typical Queries**:
```
- "What is our current product roadmap for Q1 2025?"
- "What customer feedback have we received about the alerting UI?"
- "What are the top 10 feature requests from enterprise customers?"
- "How does our pricing compare to competitors?"
- "What technical considerations should we account for in the mobile app?"
```

**Security Considerations**:
- Product managers should NOT access SRE runbooks or incident details
- Should NOT see salary data or HR performance reviews
- May need occasional access to engineering docs (granted on case-by-case basis)

---

### 4. HR Specialist

**Fictional Persona**: Maria Rodriguez, HR Business Partner

**Background**:
- 8 years in HR roles at tech companies
- Manages recruiting, benefits, and employee relations
- Handles sensitive employee data
- Ensures compliance with labor laws

**Daily Responsibilities**:
- Manage recruiting pipelines and candidate experience
- Administer benefits programs (health, 401k, equity)
- Conduct new hire onboarding
- Handle employee relations issues
- Manage performance review cycles
- Ensure compliance (SOC 2, labor laws, GDPR)
- Maintain HR policies and documentation

**Information Needs**:
- **Salary bands**: "What are the salary ranges for senior engineers?"
- **Benefits policies**: "What is our parental leave policy?"
- **Performance reviews**: "What is the timeline for Q4 performance reviews?"
- **Onboarding**: "What is the onboarding checklist for new hires?"
- **Compliance**: "What are our GDPR compliance procedures?"
- **HR policies**: "What is the remote work policy?"

**Access Patterns**:
- ✅ **Can access**: HR docs (all levels), policies (public and internal), salary bands (confidential), performance reviews (confidential)
- ❌ **Cannot access**: Engineering docs, SRE runbooks, product roadmaps, financial projections (except HR budget)
- ⚠️ **Special cases**:
  - Can access ALL employee performance reviews (confidential level)
  - Can access salary bands and compensation data
  - Can view onboarding docs across all departments
  - Cannot access engineering/product technical docs

**Typical Queries**:
```
- "What are the salary bands for L5 engineers?"
- "What is our parental leave policy in California?"
- "How do I process a promotion in Workday?"
- "What benefits are available to contractors?"
- "What is the performance review calibration process?"
```

**Security Considerations**:
- HR has access to HIGHLY sensitive data (salaries, performance reviews)
- Access must be strictly controlled and audited
- Should NOT access technical docs (not relevant to role)
- All salary/performance review access MUST be logged

---

### 5. Manager

**Fictional Persona**: David Kim, Engineering Manager

**Background**:
- 10 years of engineering experience, 3 years in management
- Manages a team of 8 backend engineers
- Reports to Director of Engineering
- Responsible for team performance and hiring

**Daily Responsibilities**:
- Conduct 1:1s with direct reports
- Write and deliver performance reviews
- Make hiring and promotion decisions
- Set team OKRs and goals
- Manage team budget and headcount planning
- Escalate and resolve technical/people issues
- Mentor and develop team members

**Information Needs**:
- **Team performance**: "How is my team performing vs. benchmarks?"
- **Performance reviews**: "What are the calibration guidelines for reviews?"
- **Budget**: "What is my budget for Q1 hiring?"
- **Career development**: "What training resources are available for my team?"
- **HR policies**: "How do I handle a performance improvement plan?"
- **Technical docs**: "What is the architecture of the service my team owns?"

**Access Patterns**:
- ✅ **Can access**: Department-specific docs (based on manager's department), team member documents, performance reviews (direct reports only), budgets (team-level)
- ❌ **Cannot access**: Other managers' team data, executive compensation, company-wide financial projections
- ⚠️ **Special cases**:
  - **Cross-department access**: Engineering manager can access engineering AND SRE docs
  - **Performance reviews**: Can ONLY view direct reports' reviews (not peers or other teams)
  - **Budget data**: Can view team-level budgets, not company-wide financials
  - **Deprecated docs**: Can access historical docs (useful for context on team decisions)

**Typical Queries**:
```
- "What are the performance review guidelines for my team?"
- "What is my headcount allocation for Q1?"
- "How do I write a performance improvement plan?"
- "What training programs are available for senior engineers?"
- "What were the OKRs for my team last quarter?"
```

**Security Considerations**:
- Managers have ELEVATED access to direct report data
- Should NOT access other teams' performance data
- Should NOT access company-wide salary bands (only HR)
- All performance review access MUST be scoped to direct reports

---

### 6. Administrator

**Fictional Persona**: Linda Wu, IT Systems Administrator

**Background**:
- 12 years in IT administration and security
- Manages internal tools and access control
- Handles compliance and audit requests
- Works with legal and HR on data requests

**Daily Responsibilities**:
- Manage user accounts and permissions
- Configure system settings and integrations
- Handle data export requests (legal, compliance)
- Monitor access logs and security events
- Conduct periodic access reviews
- Ensure SOC 2 and GDPR compliance
- Respond to audit requests

**Information Needs**:
- **Access logs**: "Who accessed salary data in the past month?"
- **Compliance reports**: "Generate SOC 2 audit report"
- **System configuration**: "Configure SSO for new identity provider"
- **User management**: "Grant temporary access for external auditor"
- **Audit trail**: "Show all documents created in the last week"

**Access Patterns**:
- ✅ **Can access**: ALL documents, audit logs, system configuration, user data
- ❌ **No restrictions** (full administrative access)
- ⚠️ **Special considerations**:
  - All admin actions are LOGGED for audit purposes
  - Can grant/revoke access for other users
  - Can view full audit trail (who accessed what, when)
  - Can export data for compliance (GDPR, SOC 2)

**Typical Queries**:
```
- "Show all documents accessed by user X in the past 30 days"
- "Generate compliance report for SOC 2 audit"
- "Who has access to financial projections?"
- "Export all HR documents created in Q4"
- "Configure new role for contractors"
```

**Security Considerations**:
- Admins have FULL SYSTEM ACCESS
- All admin actions MUST be logged and auditable
- Admin access should be granted sparingly (principle of least privilege)
- Regular access reviews required (quarterly)
- Admin accounts should have MFA enforced

---

## Cross-Role Scenarios

### Scenario 1: New Engineer Onboarding

**Roles Involved**: Engineer (new hire), Manager, HR

**Information Flow**:
1. **HR** provides onboarding checklist and benefits info (public/internal)
2. **Manager** shares team-specific context and goals (internal)
3. **Engineer** accesses engineering setup docs, code standards (internal)
4. **Engineer** reviews recent postmortems for context (internal)

**Access Requirements**:
- New engineer needs access to public/internal engineering docs
- HR provides benefits docs (public level)
- Manager can grant access to team-specific docs

---

### Scenario 2: Production Incident Response

**Roles Involved**: SRE (on-call), Engineer (owner), Manager (escalation)

**Information Flow**:
1. **SRE** receives alert, checks incident runbook (SRE-only, restricted)
2. **SRE** reviews recent postmortems for similar issues (internal)
3. **Engineer** checks service architecture docs (internal)
4. **Manager** informed if P0, reviews escalation procedures (internal)

**Access Requirements**:
- SRE needs full access to incident runbooks (including deprecated)
- Engineer needs access to service design docs
- Manager needs visibility into incident status

---

### Scenario 3: Product Planning

**Roles Involved**: Product Manager, Engineer (tech lead), Manager

**Information Flow**:
1. **Product Manager** drafts roadmap based on customer feedback (product docs)
2. **Engineer** reviews technical feasibility (engineering docs)
3. **Manager** approves team capacity allocation (internal)
4. **Product Manager** finalizes roadmap with engineering input

**Access Requirements**:
- Product Manager needs product docs (roadmaps, specs)
- Engineer needs cross-functional access to product requirements
- Both need to collaborate on feasibility docs

---

### Scenario 4: Performance Review Cycle

**Roles Involved**: Manager, HR, Employee

**Information Flow**:
1. **HR** shares performance review process guide (HR docs, internal)
2. **Manager** writes reviews for direct reports (confidential)
3. **HR** reviews for compensation alignment (confidential)
4. **Employee** receives feedback from manager

**Access Requirements**:
- Manager can ONLY access direct reports' reviews
- HR can access ALL performance reviews
- Employees can access ONLY their own reviews

---

## Access Level Hierarchy

```
┌─────────────────────────────────────────────┐
│              CONFIDENTIAL                    │  Leadership financials
│      (HR, Leadership, Admin only)            │  Salary bands
│                                              │  Security incidents
├──────────────────────────────────────────────┤
│              RESTRICTED                      │  SRE runbooks
│    (Role-specific, senior roles)             │  Product roadmap v2
│                                              │  Critical incidents
├──────────────────────────────────────────────┤
│              INTERNAL                        │  Engineering docs
│       (Department or role-based)             │  Postmortems
│                                              │  Design docs
├──────────────────────────────────────────────┤
│              PUBLIC                          │  Onboarding guides
│        (All authenticated users)             │  Company policies
│                                              │  Public wikis
└──────────────────────────────────────────────┘
```

**Access Level Definitions**:
- **PUBLIC**: All authenticated CloudSignal employees
- **INTERNAL**: Department-specific or role-specific (most common)
- **RESTRICTED**: Senior roles, specific departments, or explicit grants
- **CONFIDENTIAL**: HR, Leadership, Admin only (most sensitive)

---

## Manager Access Scoping

Managers have **department-specific access** based on their organizational role:

| Manager Type | Access Scope |
|--------------|--------------|
| Engineering Manager | Engineering + SRE docs (internal), team member data |
| SRE Manager | SRE + Engineering docs (internal), incident data |
| Product Manager | Product docs (all levels), limited engineering access |
| HR Manager | All HR docs (confidential), cross-department policies |
| Executive (VP+) | All department docs (up to restricted level) |

**Manager-Specific Permissions**:
- ✅ Can view direct reports' performance reviews
- ✅ Can access team-level budget data
- ✅ Can view documents created by team members
- ❌ Cannot view other teams' performance data
- ❌ Cannot access company-wide financial projections (unless exec)

---

## RBAC Design Principles

1. **Principle of Least Privilege**: Users get minimum access needed for their role
2. **Need-to-Know Basis**: Access is granted based on job function
3. **Separation of Duties**: Sensitive operations require multiple roles (e.g., HR + Manager for promotions)
4. **Audit Everything**: All access to confidential data is logged
5. **Time-Bounded Access**: Temporary access grants expire automatically
6. **Defense in Depth**: Multiple layers of security (RBAC + audit logs + encryption)

---

## Next Steps

This role definition will be used to create:
1. **RBAC Matrix** (STEP 2): Role × Document Type × Access Level
2. **Security Tests** (STEP 2): Validate unauthorized access is blocked
3. **Evaluation Dataset** (STEP 6): Role-specific queries for testing

---

**Version**: 1.0.0
**Last Updated**: 2025-01-01
**Maintained By**: CloudSignal Knowledge Assistant Team
**Related Documents**: [RBAC Matrix](rbac-matrix.md), [Security Model](security-model.md)
