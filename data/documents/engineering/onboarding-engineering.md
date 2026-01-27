# Engineering Onboarding Guide

**Version:** 2.1.0
**Last Updated:** 2025-01-20
**Owner:** Engineering Operations
**Status:** Active

## Welcome to CloudSignal Engineering!

Congratulations on joining CloudSignal! This guide will help you get set up and productive in your first weeks.

## First Day Checklist

### Access & Accounts

- [ ] Okta SSO account activated
- [ ] GitHub organization access (@cloudsignal)
- [ ] Slack workspace joined (#engineering, #your-team)
- [ ] Jira access for your team board
- [ ] 1Password vault access
- [ ] AWS console access (read-only to start)

### Equipment Setup

- [ ] MacBook Pro configured with IT
- [ ] Development environment installed (see below)
- [ ] VPN configured for production access
- [ ] Yubikey enrolled for 2FA

## Development Environment Setup

### Prerequisites

Install these tools via Homebrew:

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install development tools
brew install python@3.11 node@20 docker docker-compose
brew install kubectl helm terraform awscli
brew install git gh jq yq

# Install Python package manager
pip install poetry

# Install Node package manager
npm install -g pnpm
```

### Clone Repositories

```bash
# Clone main repositories
git clone git@github.com:cloudsignal/monolith.git
git clone git@github.com:cloudsignal/frontend.git
git clone git@github.com:cloudsignal/infrastructure.git

# Set up Git identity
git config --global user.name "Your Name"
git config --global user.email "your.name@cloudsignal.io"
```

### Backend Setup

```bash
cd monolith

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Start local services (Postgres, Redis, Kafka)
docker-compose up -d

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev

# Open http://localhost:3000
```

## First Week Goals

### Day 1-2: Environment & Context

- Complete development setup
- Read [Platform Architecture Overview](/docs/architecture)
- Meet with your manager and team
- Review team's current sprint goals

### Day 3-4: First Contribution

- Pick a "good first issue" from Jira
- Make your first PR
- Get familiar with code review process
- Attend team standup and planning

### Day 5: Deep Dive

- Shadow an on-call engineer
- Review recent postmortems
- Explore monitoring dashboards
- Ask questions!

## Key Documentation

| Topic | Link |
|-------|------|
| Architecture Overview | `/docs/architecture` |
| API Documentation | `/docs/api` |
| Python Style Guide | `/docs/python-style` |
| Deployment Guide | `/docs/deployment` |
| On-Call Handbook | `/docs/oncall` |

## Team Structure

### Engineering Teams

- **Backend Platform:** Core services, APIs, data pipelines
- **Frontend & UI:** Dashboard, visualization, user experience
- **Data Infrastructure:** Metrics storage, query engine
- **Machine Learning:** Anomaly detection, forecasting
- **Security:** Authentication, authorization, compliance

### Key Contacts

| Role | Name | Slack |
|------|------|-------|
| VP Engineering | David Kim | @david.kim |
| Your Manager | (Check with HR) | - |
| Engineering Buddy | (Assigned Day 1) | - |
| IT Support | IT Team | #it-help |

## Development Workflow

### Branch Naming

```
feature/JIRA-123-add-dashboard-widget
bugfix/JIRA-456-fix-auth-redirect
hotfix/JIRA-789-critical-fix
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with atomic commits
3. Push branch and create PR
4. Request review from 2 team members
5. Address feedback
6. Merge when approved (squash commits)

### Code Review Guidelines

- Respond to reviews within 24 hours
- Be constructive and specific
- Approve only when all comments addressed
- Use "Request changes" for blocking issues

## Getting Help

- **Technical questions:** Ask in #engineering or your team channel
- **Process questions:** Ask your manager or buddy
- **IT issues:** #it-help or it@cloudsignal.io
- **HR questions:** #people-ops or hr@cloudsignal.io

## Common Issues

| Issue | Solution |
|-------|----------|
| Docker not starting | `docker system prune -a` and restart Docker |
| Poetry install fails | Delete `poetry.lock` and retry |
| Can't access AWS | Request access via #it-help |
| VPN not connecting | Check Okta MFA, restart VPN client |

## Resources

- [CloudSignal Notion](https://notion.cloudsignal.io)
- [Engineering Wiki](https://wiki.cloudsignal.io/engineering)
- [Learning & Development](https://notion.cloudsignal.io/learning)

Welcome aboard! We're excited to have you on the team.
