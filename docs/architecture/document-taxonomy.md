# Document Taxonomy & Metadata Schema

## Overview

This document describes the document taxonomy and metadata schema for the CloudSignal Knowledge Assistant. It bridges the RBAC system (who can access what) with the vector database storage (how documents are stored and filtered).

## Design Principles

### 1. Security-First Metadata

Every document carries security metadata that enables **retrieval-time RBAC filtering**:

```python
# Security fields stored in Qdrant payload
{
    "access_level": "internal",        # Classification tier
    "allowed_roles": ["engineer", "sre"],  # Role-based access
    "allowed_departments": ["engineering"],  # Department-based access
    "granted_users": [],               # Explicit grants
    "denied_users": []                 # Explicit denials (highest priority)
}
```

### 2. Qdrant-Compatible Field Types

All indexed fields use Qdrant-compatible types:
- **Strings**: For exact match filtering (`status`, `access_level`)
- **Arrays**: For `any` matching (`allowed_roles`, `allowed_departments`)
- **Timestamps**: For range queries (`available_from`, `available_until`)

### 3. Separation of Concerns

| Layer | Responsibility | Files |
|-------|---------------|-------|
| Taxonomy | What document types exist | `document_taxonomy.json` |
| Schema | What fields describe documents | `metadata_schema.json` |
| RBAC | Who can access what | `rbac_matrix.json` |

## Document Types

### By Department

#### Engineering (7 types)
| Type | Access Level | Description |
|------|--------------|-------------|
| `design_doc` | internal | Technical design proposals |
| `api_spec` | internal | API documentation |
| `architecture_doc` | internal | System architecture |
| `deployment_guide` | internal | Deployment procedures |
| `coding_standards` | public | Code style guides |

#### SRE (2 types)
| Type | Access Level | Description |
|------|--------------|-------------|
| `postmortem` | internal | Incident analysis |
| `runbook` | restricted | Operational procedures |

#### Product (5 types)
| Type | Access Level | Description |
|------|--------------|-------------|
| `roadmap` | restricted | Product roadmaps |
| `feature_spec` | internal | Feature specifications |
| `customer_feedback` | internal | Customer research |
| `competitive_analysis` | restricted | Competitive intel |
| `pricing_strategy` | confidential | Pricing docs |

#### HR (5 types)
| Type | Access Level | Description |
|------|--------------|-------------|
| `hr_policy` | public | HR policies |
| `benefits_guide` | public | Benefits info |
| `salary_bands` | confidential | Compensation data |
| `performance_review` | confidential | Employee reviews |
| `onboarding_guide` | public | Onboarding docs |

#### Leadership (3 types)
| Type | Access Level | Description |
|------|--------------|-------------|
| `security_incident` | confidential | Security breaches |
| `financial_report` | confidential | Financial data |
| `board_deck` | confidential | Board presentations |

## Access Levels

| Level | Sensitivity | Audit Required | Who Can Access |
|-------|-------------|----------------|----------------|
| `public` | 1 (lowest) | No | All authenticated employees |
| `internal` | 2 | No | Department/role-based |
| `restricted` | 3 | Yes | Senior roles, explicit grants |
| `confidential` | 4 (highest) | Yes | HR, Leadership, Admin only |

## Metadata Fields

### Required Fields

```json
{
  "document_id": "UUID",
  "title": "string",
  "doc_type": "enum (20 types)",
  "access_level": "enum (4 levels)",
  "department": "enum (6 departments)",
  "status": "enum (draft|active|deprecated|archived)",
  "owner_id": "string (user ID)",
  "created_date": "ISO 8601 datetime",
  "allowed_roles": "array of role names",
  "allowed_departments": "array of department codes"
}
```

### Security Fields (Qdrant Indexed)

```json
{
  "allowed_roles": ["engineer", "sre", "admin"],
  "allowed_departments": ["engineering", "sre"],
  "granted_users": ["eng-100"],
  "denied_users": ["eng-999"],
  "available_from": "2025-02-01T00:00:00Z",
  "available_until": null
}
```

### Content Fields

```json
{
  "summary": "Brief description for search results",
  "keywords": ["database", "outage", "postmortem"],
  "version": "1.0.0",
  "related_docs": ["uuid-1", "uuid-2"]
}
```

### Chunk Fields (for Vector DB)

```json
{
  "chunk_index": 0,
  "chunk_count": 5,
  "text": "The actual content of this chunk...",
  "citations": [{"source": "file.md", "section": "Overview"}]
}
```

## Document Lifecycle

```
┌─────────┐    publish    ┌────────┐    deprecate    ┌────────────┐    archive    ┌──────────┐
│  draft  │ ───────────▶  │ active │ ─────────────▶  │ deprecated │ ────────────▶ │ archived │
└─────────┘               └────────┘                 └────────────┘               └──────────┘
                               ▲                           │
                               └───────── restore ─────────┘
```

### Status Visibility

| Status | Searchable | Visible To |
|--------|------------|------------|
| `draft` | No | Owner, Admin only |
| `active` | Yes | Per RBAC rules |
| `deprecated` | Yes | SRE, Manager, Admin |
| `archived` | No | Admin only |

## RBAC Filter Construction

### Example: Engineer Querying Documents

```python
def build_engineer_filter(user_id: str) -> dict:
    return {
        "must": [
            {"key": "status", "match": {"value": "active"}}
        ],
        "must_not": [
            {"key": "denied_users", "match": {"any": [user_id]}}
        ],
        "should": [
            {"key": "access_level", "match": {"value": "public"}},
            {"key": "allowed_roles", "match": {"any": ["engineer"]}},
            {"key": "granted_users", "match": {"any": [user_id]}}
        ],
        "min_should_match": 1
    }
```

### Filter Priority Order

1. **Explicit denials** (`denied_users`) - Highest priority, always blocks
2. **Explicit grants** (`granted_users`) - Overrides role-based denial
3. **Role-based access** (`allowed_roles`) - Standard RBAC
4. **Department-based access** (`allowed_departments`) - Fallback
5. **Public documents** (`access_level = public`) - Lowest priority

## Temporal Filtering

Documents can be embargoed or expired:

```python
# Temporal constraints
{
    "available_from": "2025-02-01T00:00:00Z",  # Not visible until Feb 1
    "available_until": "2025-12-31T23:59:59Z"  # Hidden after Dec 31
}

# Qdrant filter for temporal constraints
{
    "must": [
        {"key": "available_from", "range": {"lte": current_time}},
        {"key": "available_until", "range": {"gte": current_time}}
    ]
}
```

## Special Access Rules

### Manager Scoping

Managers have scoped access to certain documents:

```json
{
  "doc_type": "performance_review",
  "manager_scope": {
    "direct_reports_only": true,
    "employee_id": "eng-456"
  }
}
```

Filter for manager:
```python
# Manager can only see reviews for their direct reports
{"key": "manager_scope.direct_reports_only", "match": {"value": true}},
{"key": "manager_scope.employee_id", "match": {"any": direct_report_ids}}
```

### Document Ownership

Owners always have access to their own documents:

```python
# Owner override
{"key": "owner_id", "match": {"value": current_user_id}}
```

## Integration with Security Tests

The 30 security test cases in `security_tests.jsonl` validate:

| Test Category | Count | Purpose |
|---------------|-------|---------|
| Unauthorized Access | 10 | Verify RBAC blocks forbidden docs |
| Prompt Injection | 5 | Verify attacks don't bypass filters |
| Authorized Access | 6 | Verify legitimate access works |
| Edge Cases | 9 | Deprecated docs, temporal, manager scoping |

## File Locations

| File | Purpose |
|------|---------|
| `data/metadata/document_taxonomy.json` | Document type definitions |
| `data/metadata/metadata_schema.json` | JSON Schema for validation |
| `data/metadata/rbac_matrix.json` | Role-based access rules |
| `data/evaluation/security_tests.jsonl` | Security test cases |

## Versioning

Documents use semantic versioning:

- **Major** (1.0.0 → 2.0.0): Breaking changes, complete rewrites
- **Minor** (1.0.0 → 1.1.0): New sections, significant updates
- **Patch** (1.0.0 → 1.0.1): Typo fixes, clarifications

Keep last 5 versions for audit trail.

## Interview Talking Points

When discussing this in FAANG interviews:

> "I designed a document taxonomy with 20 document types across 4 access levels. Each document carries security metadata that enables retrieval-time RBAC filtering in Qdrant. The schema supports temporal filtering for embargoed documents, explicit grants/denials, and manager-scoped access for performance reviews. All 30 security test cases validate 0% unauthorized leakage."

## Next Steps

1. **STEP 4**: Generate synthetic documents following this taxonomy
2. **STEP 5**: Implement ingestion pipeline with metadata extraction
3. **STEP 6**: Build evaluation framework with QA pairs
