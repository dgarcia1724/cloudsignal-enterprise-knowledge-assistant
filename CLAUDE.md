# CloudSignal Enterprise Knowledge Assistant

**Project Type**: Production-Grade RAG System for FAANG Interviews
**Tech Stack**: Python/FastAPI + Next.js 15 + Qdrant + PostgreSQL + AWS
**Repository**: https://github.com/dgarcia1724/cloudsignal-enterprise-knowledge-assistant.git

## Project Overview

A secure, role-based access control (RBAC) enabled knowledge assistant for CloudSignal, a fictional B2B SaaS company (~300 employees) specializing in cloud monitoring and alerting.

**One-Line Pitch**: Secure internal knowledge assistant for cloud monitoring & incident response teams

**Goal**: Demonstrate senior full-stack engineering skills for FAANG interviews by building a production-ready RAG system with enterprise-grade security, comprehensive evaluation, and AWS deployment.

## Company Context (Fictional)

**CloudSignal Inc.**
- Industry: B2B SaaS (Cloud Monitoring & Alerting Platform)
- Size: ~300 employees
- Departments:
  - Engineering (100): Backend, frontend, mobile developers
  - SRE (30): Site reliability, DevOps, infrastructure
  - Product (40): Product managers, designers, analysts
  - HR (20): Recruiting, people ops, benefits
  - Leadership (15): Executives, board members
  - Operations (95): Sales, marketing, customer success, finance

**User Roles** (for RBAC):
1. **Engineer**: Access to engineering docs, postmortems, runbooks, design docs
2. **SRE**: Access to SRE-specific docs, incident reports, monitoring configs, engineering docs
3. **Product Manager**: Access to product roadmaps, feature specs, customer feedback
4. **HR**: Access to policies, benefits, salary bands, performance reviews
5. **Manager**: Access to team documents based on department
6. **Admin**: Full access to all documents

## Key Differentiators (FAANG Interview Selling Points)

### 1. Security-First Architecture
- **Retrieval-time RBAC enforcement**: Pre-filter vectors in Qdrant BEFORE they reach the LLM
- Zero unauthorized leakage (validated through automated testing)
- Prompt injection defense
- Comprehensive audit logging

### 2. Production-Grade Evaluation
- 50-100 QA pairs with ground truth
- Security testing (unauthorized access attempts)
- Metrics: Unauthorized leakage rate (0%), MRR, NDCG@5, faithfulness, p95 latency
- Automated evaluation in CI/CD

### 3. Hybrid Retrieval System
- BM25 + vector similarity (Reciprocal Rank Fusion)
- Two-stage retrieval: Broad recall (top-20) → Reranking (top-5)
- Citation extraction for transparency
- Handles deprecated documents and version conflicts

### 4. AWS Production Deployment
- ECS Fargate (Backend + Qdrant services)
- RDS PostgreSQL (db.t3.micro Free Tier)
- S3 document storage
- CloudWatch monitoring
- Terraform infrastructure as code
- Vercel frontend hosting (free)

### 5. Clean Architecture
- Separation of concerns (services, models, schemas, API)
- Type safety (Pydantic, TypeScript)
- Comprehensive testing (unit, integration, E2E)
- Production observability (metrics, logging, tracing)

## Cost Strategy

**Budget Target**: <$100/month typical, <$300/month max

This project is optimized for cost-effectiveness while maintaining FAANG-interview credibility. The architecture demonstrates production-ready patterns without requiring expensive always-on infrastructure.

### Monthly Cost Breakdown

| Category | Service | Est. Cost |
|----------|---------|-----------|
| **AWS Infrastructure** | | |
| Compute | ECS Fargate (Backend) - 0.25 vCPU, 0.5GB | ~$10 |
| Compute | ECS Fargate (Qdrant) - 0.5 vCPU, 1GB | ~$20 |
| Database | RDS PostgreSQL db.t3.micro (Free Tier) | $0 |
| Storage | S3 < 5GB (Free Tier) | $0 |
| Secrets | AWS Secrets Manager | ~$2 |
| Monitoring | CloudWatch (basic) | ~$5 |
| **Frontend** | Vercel (Free Tier) | $0 |
| **APIs** | | |
| Embeddings | OpenAI text-embedding-3-small | ~$0.10 |
| LLM | OpenAI GPT-4o-mini (~5K queries/mo) | ~$15 |
| **Total** | | **~$50-75/mo** |

### Cost Optimization Techniques

1. **Free Tier Maximization**: RDS db.t3.micro (750 hrs/mo free), S3 (5GB free), Vercel (free hosting)
2. **Efficient Models**: GPT-4o-mini instead of GPT-4 (10x cheaper), text-embedding-3-small instead of large (6x cheaper)
3. **Local Reranking**: Cross-encoder runs on ECS instead of paid Cohere API
4. **Response Caching**: Cache frequent queries to reduce API calls
5. **Single Environment**: One AWS environment instead of Dev/Staging/Prod

## Tech Stack Rationale

| Component | Technology | Why? |
|-----------|-----------|------|
| Backend | Python + FastAPI | Async/await, automatic OpenAPI docs, ML ecosystem |
| Vector DB | Qdrant | Self-hosted on ECS, payload filtering for RBAC, HNSW performance |
| Frontend | Next.js 15 (App Router) | Modern React, SSR, hosted on Vercel (free) |
| Database | PostgreSQL | ACID, JSONB support, RDS Free Tier (db.t3.micro) |
| Embeddings | OpenAI text-embedding-3-small | Cost-effective (1536 dim), excellent quality |
| LLM | OpenAI GPT-4o-mini | Best cost/performance ($0.15/1M input tokens) |
| Reranker | Cross-encoder (sentence-transformers) | Local inference, no API cost |
| Cloud | AWS | Industry standard, interview relevance |
| IaC | Terraform | Declarative, state management |

## Code Conventions

### Python (Backend)

**Style**:
- Black formatter (line length 100)
- Ruff linter
- Type hints required (mypy strict mode)
- Docstrings for public functions (Google style)

**Naming**:
- Classes: `PascalCase` (e.g., `DocumentMetadata`)
- Functions/methods: `snake_case` (e.g., `build_rbac_filter`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_CHUNK_SIZE`)
- Private methods: `_leading_underscore` (e.g., `_compute_metrics`)

**Imports**:
```python
# Standard library
import os
from typing import List, Optional

# Third-party
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# Local
from app.core import auth
from app.services import retrieval
```

**Async/Await**:
- Use `async def` for I/O operations (database, API calls, file I/O)
- Use `await` for async calls
- Prefer `asyncio.gather()` for parallel operations

### TypeScript (Frontend)

**Style**:
- Prettier formatter
- ESLint
- Strict TypeScript mode
- React functional components with hooks

**Naming**:
- Components: `PascalCase` (e.g., `ChatInterface.tsx`)
- Functions: `camelCase` (e.g., `useChatStream`)
- Types/Interfaces: `PascalCase` (e.g., `MessageType`, `UserContext`)
- Constants: `UPPER_SNAKE_CASE` or `camelCase` for config

**Component Structure**:
```typescript
// Types
interface Props {
  ...
}

// Component
export function ComponentName({ ...props }: Props) {
  // Hooks
  const [state, setState] = useState(...)

  // Effects
  useEffect(() => { ... }, [deps])

  // Handlers
  const handleClick = () => { ... }

  // Render
  return (...)
}
```

### Git Commit Messages

Format: `<type>(<scope>): <subject>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build, deps, configs
- `security`: Security improvements

Examples:
```
feat(rbac): implement retrieval-time RBAC filtering
fix(chat): resolve streaming message duplication
docs(architecture): add RBAC security model diagram
test(evaluation): add unauthorized access test cases
```

## Project Structure

```
cloudsignal-enterprise-knowledge-assistant/
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/              # API routes
│   │   ├── core/                # Auth, RBAC, security
│   │   ├── models/              # SQLAlchemy ORM
│   │   ├── schemas/             # Pydantic DTOs
│   │   ├── services/            # Business logic
│   │   │   ├── ingestion/       # Document parsing, chunking, embedding
│   │   │   ├── retrieval/       # Hybrid search, reranking
│   │   │   ├── generation/      # LLM integration
│   │   │   └── evaluation/      # Metrics, testing
│   │   ├── db/                  # Database, migrations
│   │   └── vector_store/        # Qdrant client
│   ├── evaluation/              # Evaluation framework
│   ├── tests/                   # Unit, integration, E2E tests
│   └── scripts/                 # Utility scripts
│
├── frontend/                    # Next.js 15 frontend
│   ├── src/
│   │   ├── app/                 # App Router (Next.js 15)
│   │   ├── components/          # React components
│   │   ├── lib/                 # Utilities, API client
│   │   ├── hooks/               # Custom React hooks
│   │   └── types/               # TypeScript types
│   └── tests/                   # Component tests, E2E
│
├── infrastructure/              # DevOps, IaC
│   └── terraform/               # AWS infrastructure (networking, compute, database)
│
├── data/                        # Datasets
│   ├── documents/               # Synthetic CloudSignal docs
│   ├── evaluation/              # QA pairs, test cases
│   └── metadata/                # RBAC matrix, taxonomy
│
├── docs/                        # Documentation
│   ├── architecture/            # System design, security model
│   ├── api/                     # API documentation
│   └── evaluation/              # Metrics, methodology
│
├── scripts/                     # Cross-project scripts
└── .github/workflows/           # CI/CD
```

## Development Workflow

### Prerequisites

- Python 3.11+
- Node.js 20+
- AWS CLI configured
- Terraform
- Poetry (Python dependency management)
- pnpm (Node package manager)

### Setup

```bash
# Backend
cd backend
poetry install

# Frontend
cd frontend
pnpm install

# Deploy infrastructure
cd infrastructure/terraform
terraform init
terraform apply
```

### Environment Variables

- Use AWS Secrets Manager for all secrets (API keys, DB credentials)
- Never commit `.env` files
- Access secrets via AWS SDK in application code

### Testing

**Backend**:
```bash
cd backend
poetry run pytest tests/unit       # Unit tests
poetry run pytest tests/integration # Integration tests
poetry run pytest tests/e2e         # End-to-end tests
poetry run pytest --cov=app         # Coverage report
```

**Frontend**:
```bash
cd frontend
pnpm test         # Jest unit tests
pnpm test:e2e     # Playwright E2E tests
```

**Security Tests** (CRITICAL):
```bash
cd backend
poetry run pytest tests/test_rbac_evaluation.py -v
# MUST achieve 0% unauthorized leakage rate
```

### Code Quality

**Pre-commit Hooks** (enforced):
- Black (Python formatting)
- Ruff (Python linting)
- mypy (Python type checking)
- Prettier (TypeScript/TSX formatting)
- ESLint (TypeScript linting)
- No hardcoded secrets

**Manual Checks**:
```bash
# Backend
make lint      # Run ruff, black, mypy
make format    # Auto-format code
make test      # Run all tests

# Frontend
make lint-fe   # Run ESLint, Prettier check
make format-fe # Auto-format code
make test-fe   # Run all tests
```

## Security Practices

### CRITICAL: RBAC Enforcement

**NEVER filter documents after retrieval**. Always enforce RBAC at query time:

```python
# ❌ WRONG - Documents already in LLM context
results = qdrant.search(query_vector=embedding)
filtered = [r for r in results if user_can_access(r)]

# ✅ CORRECT - Filter BEFORE search
rbac_filter = build_rbac_filter(user_context)
results = qdrant.search(
    query_vector=embedding,
    query_filter=rbac_filter  # Security enforced HERE
)
```

### Secrets Management

- **Never** commit API keys, passwords, or secrets
- Use environment variables (local)
- Use AWS Secrets Manager (production)
- Use `.env.example` for documentation
- GitHub secret scanning enabled

### Audit Logging

Log all security-relevant events:
- Access denials (RBAC violations)
- Prompt injection attempts
- Sensitive document access (HR, Leadership docs)
- User authentication events

## Monitoring & Observability

### Metrics (CloudWatch)

Track:
- RBAC denials by role/document type
- Query latency (p50, p95)
- API error rates
- LLM token usage

### Logging (Structured JSON)

Include in every log:
- `trace_id`: Request trace ID
- `user_id`: Authenticated user
- `role`: User's role
- `timestamp`: ISO 8601
- `level`: INFO, WARNING, ERROR
- `message`: Human-readable

### Alerts (CloudWatch)

Alert on:
- High error rate (>5%)
- P95 latency spike (>10s)
- ECS task failures

## Deployment

### Environment

**Single AWS Environment** (cost-optimized, production-ready architecture)

| Service | Configuration | Purpose |
|---------|--------------|---------|
| ECS Fargate | 2 services (Backend + Qdrant) | Compute |
| RDS PostgreSQL | db.t3.micro (Free Tier) | Database |
| S3 | Single bucket | Document storage |
| Secrets Manager | API keys, DB credentials | Secrets |
| CloudWatch | Basic logs and metrics | Monitoring |
| Vercel | Connected to GitHub | Frontend hosting |

### CI/CD Pipeline (GitHub Actions)

**On Pull Request**:
- Lint & format checks (Ruff, Black, ESLint, Prettier)
- Unit tests
- **RBAC security tests** (MUST pass, 0% leakage)

**On Merge to Main**:
- All PR checks
- Build & push Docker images to ECR
- Deploy to ECS
- Run smoke tests
- Vercel auto-deploys frontend

### Infrastructure as Code

Terraform modules (3 total):
- `networking/` - VPC, security groups, subnets
- `compute/` - ECS cluster, task definitions, services
- `database/` - RDS PostgreSQL instance

## Common Commands (Makefile)

```bash
# Development
make setup          # Install dependencies (backend + frontend)
make test           # Run all tests
make lint           # Run all linters
make format         # Auto-format all code

# Data
make ingest         # Ingest sample documents
make eval           # Run evaluation suite
make seed           # Seed database with users/roles

# Infrastructure
make infra-plan     # Terraform plan
make infra-apply    # Terraform apply
make infra-destroy  # Terraform destroy

# Deployment
make build          # Build Docker images
make deploy         # Deploy to AWS ECS
```

## Interview Talking Points

When discussing this project in FAANG interviews:

1. **Security-First**: "I enforced RBAC at retrieval time using Qdrant payload filtering, ensuring unauthorized documents never reach the LLM context. Validated with 0% unauthorized leakage rate."

2. **Evaluation Rigor**: "I built the evaluation framework FIRST with 50-100 QA pairs covering security, retrieval quality, and edge cases. Runs in CI/CD on every PR."

3. **Production-Ready Architecture**: "AWS deployment with ECS Fargate, RDS PostgreSQL, Terraform IaC. Architecture designed for Multi-AZ scaling - can discuss trade-offs between cost and high availability."

4. **Cost Optimization**: "Reduced infrastructure costs 90% using Free Tier services and efficient models (GPT-4o-mini, text-embedding-3-small). Two-stage retrieval with local cross-encoder reranking eliminates API costs."

5. **Systems Thinking**: "Idempotent ingestion pipeline with document hashing and versioning. Hybrid retrieval (BM25 + vector) with Reciprocal Rank Fusion for robust results."

## Resources

- **Plan**: `.claude/plans/gentle-purring-feigenbaum.md`
- **Architecture Diagrams**: `docs/architecture/system-design.md`
- **API Documentation**: Auto-generated at `/docs` (FastAPI)
- **Evaluation Results**: `backend/evaluation/reports/`

## Notes for Claude

- Prioritize security over convenience
- Follow the 9-step plan sequentially
- Update todos as tasks are completed
- Write tests BEFORE implementation for critical components
- Document all RBAC decisions
- Keep README updated with progress
- Focus on FAANG-worthy design decisions

---

**Current Status**: STEPS 0-2 complete (Company Profile, Role Personas, RBAC Matrix, Security Model)

**Next Steps**:
1. Document taxonomy & metadata schema (STEP 3)
2. Generate synthetic dataset (STEP 4)
3. Retrieval strategy documentation (STEP 5)
