# CloudSignal Platform Architecture Overview

**Version:** 2.0.0
**Last Updated:** 2024-12-10
**Author:** Architecture Team
**Status:** Active

## Executive Summary

CloudSignal is a cloud-native monitoring and alerting platform that processes billions of metrics daily from thousands of enterprise customers. This document provides a comprehensive overview of our system architecture.

## High-Level Architecture

```
                           ┌─────────────────────────────────────┐
                           │         CloudSignal Platform         │
                           └─────────────────────────────────────┘

    ┌──────────────┐       ┌─────────────────────────────────────┐
    │   Metrics    │──────►│            Load Balancer            │
    │   Agents     │       │          (AWS ALB/NLB)              │
    └──────────────┘       └────────────────┬────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
              ┌─────▼─────┐          ┌──────▼──────┐         ┌──────▼──────┐
              │  API      │          │  Metrics    │         │  Dashboard  │
              │  Gateway  │          │  Ingest     │         │  Service    │
              └─────┬─────┘          └──────┬──────┘         └──────┬──────┘
                    │                       │                       │
                    │                       ▼                       │
                    │               ┌──────────────┐                │
                    │               │    Kafka     │                │
                    │               │   Cluster    │                │
                    │               └──────┬───────┘                │
                    │                      │                        │
                    ▼                      ▼                        ▼
              ┌──────────┐         ┌──────────────┐         ┌──────────────┐
              │PostgreSQL│         │ TimescaleDB  │         │    Redis     │
              │ (Users)  │         │  (Metrics)   │         │   (Cache)    │
              └──────────┘         └──────────────┘         └──────────────┘
```

## Core Components

### 1. Metrics Ingestion Layer

**Purpose:** Receive, validate, and store metrics from customer agents

**Components:**
- **Metrics Gateway:** Receives HTTP/gRPC metric submissions
- **Kafka Producers:** Buffer metrics for downstream processing
- **Validation Service:** Checks metric format and quotas

**Scale:**
- 10M+ metrics per minute
- 12 Kafka brokers
- 64 partitions for high parallelism

### 2. Stream Processing Layer

**Purpose:** Real-time metric aggregation and alert evaluation

**Components:**
- **Apache Flink Cluster:** Stream processing engine
- **Rule Engine:** Evaluates alert conditions
- **Aggregation Service:** Computes rollups (1m, 5m, 1h, 1d)

**Capabilities:**
- Sub-second alert latency
- Complex event processing
- Stateful computations

### 3. Storage Layer

**Purpose:** Persist metrics, metadata, and user data

| Database | Purpose | Technology |
|----------|---------|------------|
| TimescaleDB | Time-series metrics | PostgreSQL extension |
| PostgreSQL | User data, configs | RDS Multi-AZ |
| Redis Cluster | Caching, sessions | ElastiCache |
| S3 | Long-term storage | AWS S3 Glacier |

### 4. API Layer

**Purpose:** Serve customer requests and internal services

**Components:**
- **API Gateway:** Request routing, rate limiting
- **REST API:** Customer-facing endpoints
- **GraphQL API:** Dashboard queries
- **gRPC:** Internal service communication

### 5. Frontend Layer

**Purpose:** User interface for dashboards and configuration

**Technology:**
- Next.js 15 (React)
- Server-side rendering
- Real-time updates via WebSocket

## Data Flow

### Metric Ingestion Flow

1. Agent sends metrics to Metrics Gateway (HTTPS)
2. Gateway validates and enriches metric data
3. Metrics published to Kafka topic `metrics.raw`
4. Flink consumes and aggregates metrics
5. Aggregated metrics stored in TimescaleDB
6. Alert rules evaluated in real-time

### Query Flow

1. User requests dashboard data
2. API Gateway routes to Dashboard Service
3. Service checks Redis cache
4. Cache miss → Query TimescaleDB
5. Results cached and returned

## Infrastructure

### AWS Services

| Service | Purpose |
|---------|---------|
| EKS | Kubernetes orchestration |
| RDS | PostgreSQL databases |
| ElastiCache | Redis caching |
| MSK | Managed Kafka |
| S3 | Object storage |
| CloudFront | CDN for static assets |

### Kubernetes Namespaces

```
├── production
│   ├── api-gateway
│   ├── metrics-service
│   ├── alerting-service
│   └── dashboard-service
├── infrastructure
│   ├── kafka-connect
│   ├── flink-cluster
│   └── monitoring
└── platform
    ├── cert-manager
    ├── ingress-nginx
    └── external-dns
```

## Security Architecture

### Network Security

- VPC with private subnets
- Security groups per service
- WAF for API protection
- TLS 1.3 for all traffic

### Authentication

- OAuth 2.0 / OIDC for users
- API keys for service access
- mTLS for internal services

### Data Protection

- Encryption at rest (AES-256)
- Encryption in transit (TLS)
- Customer data isolation

## Reliability

### High Availability

- Multi-AZ deployments
- Database replication
- Kafka replication factor 3
- Auto-scaling policies

### Disaster Recovery

- RPO: 1 hour
- RTO: 4 hours
- Cross-region backups
- Automated failover

## Monitoring

### Internal Monitoring

We use CloudSignal to monitor CloudSignal (dogfooding):

- Infrastructure metrics
- Application metrics
- Business metrics
- SLO dashboards

### Key SLOs

| Service | SLO | Current |
|---------|-----|---------|
| API Availability | 99.9% | 99.95% |
| Metric Ingestion Latency | < 5s p99 | 2.3s |
| Alert Delivery | < 60s p99 | 12s |
| Dashboard Load Time | < 3s p95 | 1.8s |

## Future Architecture

See [RFC: Microservices Migration](/docs/rfc-microservices) for planned architectural changes.
