# Q4 2024 Customer Feedback Summary

**Version:** 1.0.0
**Last Updated:** 2025-01-15
**Owner:** Product Management
**Status:** Active

## Executive Summary

Q4 2024 feedback analysis covers 523 active customers, 1,247 support tickets, 89 customer interviews, and NPS surveys. Key themes: dashboard customization, alert noise reduction, and enterprise collaboration features.

## NPS Overview

| Segment | Q3 2024 | Q4 2024 | Change |
|---------|---------|---------|--------|
| Enterprise | 45 | 48 | +3 |
| Mid-Market | 42 | 44 | +2 |
| SMB | 38 | 40 | +2 |
| **Overall** | **42** | **44** | **+2** |

### NPS Breakdown

- Promoters (9-10): 52% (+2%)
- Passives (7-8): 28% (-1%)
- Detractors (0-6): 20% (-1%)

## Top Feature Requests

### Ranked by Customer Mentions

| Rank | Feature | Mentions | Segment |
|------|---------|----------|---------|
| 1 | Custom Dashboards | 156 | Enterprise |
| 2 | Alert Noise Reduction | 134 | All |
| 3 | Team Workspaces | 98 | Enterprise |
| 4 | API Improvements | 87 | Developer |
| 5 | Mobile App | 72 | All |

### Feature Request Details

#### 1. Custom Dashboards (156 mentions)

**Customer Quotes:**
> "We need to build dashboards that match our internal taxonomy, not CloudSignal's default views." - Enterprise Customer, FinTech

> "The current dashboard is one-size-fits-all. We have different needs for DevOps vs. management." - Mid-Market, Healthcare

**Requirements Identified:**
- Drag-and-drop layout
- Custom widget types
- Dashboard variables
- Team-specific views

**Roadmap Status:** Q1 2025 (Custom Dashboards v2)

#### 2. Alert Noise Reduction (134 mentions)

**Customer Quotes:**
> "We get 500 alerts per day. Maybe 10 are actionable. The rest are noise." - SRE, E-commerce

> "Alert fatigue is real. Our team is starting to ignore alerts." - DevOps Lead, SaaS

**Requirements Identified:**
- Automatic threshold adjustment
- Alert correlation/grouping
- Smarter notification routing
- Alert suppression rules

**Roadmap Status:** Q1-Q2 2025 (Intelligent Alerting)

#### 3. Team Workspaces (98 mentions)

**Customer Quotes:**
> "We have 15 teams. They're stepping on each other's dashboards and alerts." - Platform Lead, Enterprise

> "Need isolation between production and development monitoring." - Engineering Manager

**Requirements Identified:**
- Team-level isolation
- RBAC improvements
- Per-team billing
- Cross-team sharing controls

**Roadmap Status:** Q2 2025 (Team Workspaces)

## Support Ticket Analysis

### Ticket Volume by Category

| Category | Q3 | Q4 | Change |
|----------|-----|-----|--------|
| Dashboard Issues | 312 | 287 | -8% |
| Alert Configuration | 245 | 298 | +22% |
| Integration Problems | 178 | 156 | -12% |
| Performance | 134 | 123 | -8% |
| Billing | 89 | 78 | -12% |

### Top Support Issues

1. **Alert threshold tuning** (112 tickets)
   - Customers struggle to set appropriate thresholds
   - Request: automatic baseline learning

2. **Dashboard slow loading** (87 tickets)
   - Large dashboards with many widgets
   - Request: performance optimization

3. **Slack integration failures** (65 tickets)
   - Token expiration issues
   - Request: better error messaging

## Customer Interviews

### Interview Summary (89 sessions)

| Segment | Interviews | Key Theme |
|---------|------------|-----------|
| Enterprise | 34 | Scalability, compliance |
| Mid-Market | 32 | Ease of use, value |
| SMB | 23 | Getting started, cost |

### Key Insights

#### Enterprise Customers

1. **Data Residency:** 8 of 34 enterprise customers require EU data residency
2. **SSO/SAML:** All enterprise customers use SSO; 5 reported integration issues
3. **SLA Requirements:** 12 customers need 99.99% SLA (currently 99.9%)

#### Mid-Market Customers

1. **Onboarding:** Average time to first dashboard is 25 minutes (target: 10)
2. **Template Need:** 78% would use pre-built templates if available
3. **Cost Sensitivity:** Price is top 3 concern for 60% of this segment

### Churn Risk Indicators

| Indicator | At-Risk Customers | Action |
|-----------|-------------------|--------|
| Low engagement (<1 login/week) | 23 | Success outreach |
| High ticket volume (>5/month) | 12 | Executive escalation |
| Competitor evaluation | 8 | Retention offers |

## Competitive Mentions

| Competitor | Mentions | Context |
|------------|----------|---------|
| Datadog | 45 | Feature comparison |
| New Relic | 23 | Price comparison |
| Grafana | 18 | Open-source alternative |
| Prometheus | 15 | DIY consideration |

### Competitive Win/Loss

| Outcome | Count | Top Reason |
|---------|-------|------------|
| Won vs Datadog | 12 | Price, simplicity |
| Lost to Datadog | 8 | Feature depth |
| Won vs New Relic | 7 | Performance |
| Lost to Grafana | 5 | Cost (open source) |

## Recommendations

### Immediate (Q1 2025)

1. **Launch Custom Dashboards v2** - Address #1 feature request
2. **Improve onboarding** - Reduce time to first dashboard to 10 min
3. **Add dashboard templates** - 20+ templates for common use cases

### Near-term (Q2 2025)

1. **Intelligent Alerting** - ML-based thresholds and correlation
2. **Team Workspaces** - Address enterprise isolation needs
3. **EU Data Residency** - Enable European deployment

### Long-term (H2 2025)

1. **Mobile App** - Native iOS/Android experience
2. **99.99% SLA** - Infrastructure improvements
3. **Integration Marketplace** - Third-party ecosystem

## Appendix

### Survey Methodology

- NPS Survey: Sent monthly to all active users
- Response rate: 34%
- Customer interviews: Scheduled via success team
- Support ticket analysis: Automated categorization + manual review

### References

- [Full Interview Transcripts](/docs/research/interviews-q4)
- [NPS Raw Data](/docs/data/nps-q4-2024)
- [Support Ticket Export](/docs/data/tickets-q4-2024)
