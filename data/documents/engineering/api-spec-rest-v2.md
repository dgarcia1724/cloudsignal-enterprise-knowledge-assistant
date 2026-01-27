# CloudSignal REST API v2 Specification

**Version:** 2.3.0
**Last Updated:** 2025-01-05
**Status:** Active
**Base URL:** `https://api.cloudsignal.io/v2`

## Authentication

All API requests require authentication via API key or OAuth2 token.

### API Key Authentication

Include your API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: cs_live_abc123..." \
     https://api.cloudsignal.io/v2/metrics
```

### OAuth2 Bearer Token

For user-context requests, use Bearer token:

```bash
curl -H "Authorization: Bearer eyJhbGc..." \
     https://api.cloudsignal.io/v2/dashboards
```

## Rate Limiting

| Plan | Requests/min | Burst |
|------|--------------|-------|
| Free | 60 | 10 |
| Pro | 600 | 100 |
| Enterprise | 6000 | 1000 |

Rate limit headers:
- `X-RateLimit-Limit`: Max requests per window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp of reset

## Endpoints

### Metrics

#### Submit Metrics

```http
POST /v2/metrics
Content-Type: application/json

{
  "metrics": [
    {
      "name": "cpu.usage",
      "value": 85.5,
      "timestamp": 1704067200,
      "tags": {
        "host": "prod-web-01",
        "region": "us-east-1"
      }
    }
  ]
}
```

**Response:**
```json
{
  "accepted": 1,
  "rejected": 0,
  "request_id": "req_abc123"
}
```

#### Query Metrics

```http
GET /v2/metrics/query
  ?metric=cpu.usage
  &start=1704067200
  &end=1704153600
  &aggregation=avg
  &interval=5m
  &tags=host:prod-web-01
```

**Response:**
```json
{
  "metric": "cpu.usage",
  "data": [
    {"timestamp": 1704067200, "value": 45.2},
    {"timestamp": 1704067500, "value": 52.1}
  ]
}
```

### Alerts

#### List Alert Rules

```http
GET /v2/alerts/rules
```

**Response:**
```json
{
  "rules": [
    {
      "id": "rule_abc123",
      "name": "High CPU Usage",
      "condition": "avg(cpu.usage) > 90",
      "severity": "critical",
      "enabled": true
    }
  ],
  "pagination": {
    "total": 42,
    "page": 1,
    "per_page": 20
  }
}
```

#### Create Alert Rule

```http
POST /v2/alerts/rules
Content-Type: application/json

{
  "name": "High Memory Usage",
  "condition": "avg(memory.usage) > 85",
  "severity": "warning",
  "notification_channels": ["slack_engineering"],
  "cooldown_minutes": 15
}
```

### Dashboards

#### List Dashboards

```http
GET /v2/dashboards
```

#### Get Dashboard

```http
GET /v2/dashboards/{dashboard_id}
```

#### Create Dashboard

```http
POST /v2/dashboards
Content-Type: application/json

{
  "name": "Production Overview",
  "widgets": [
    {
      "type": "timeseries",
      "metric": "http.request_count",
      "aggregation": "sum",
      "position": {"x": 0, "y": 0, "w": 6, "h": 4}
    }
  ]
}
```

### Webhooks

#### Create Webhook

```http
POST /v2/webhooks
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["alert.triggered", "alert.resolved"],
  "secret": "whsec_abc123..."
}
```

#### Webhook Payload

```json
{
  "event": "alert.triggered",
  "timestamp": 1704067200,
  "data": {
    "alert_id": "alert_xyz789",
    "rule_id": "rule_abc123",
    "severity": "critical",
    "message": "CPU usage exceeded 90%",
    "metric_value": 95.2
  },
  "signature": "sha256=abc123..."
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "request_id": "req_abc123"
  }
}
```

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | INVALID_REQUEST | Malformed request body |
| 401 | UNAUTHORIZED | Invalid or missing API key |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

## SDKs

- [Python SDK](https://github.com/cloudsignal/python-sdk)
- [Node.js SDK](https://github.com/cloudsignal/node-sdk)
- [Go SDK](https://github.com/cloudsignal/go-sdk)

## Changelog

- **2.3.0** (2025-01-05): Added webhook signature verification
- **2.2.0** (2024-11-15): Added dashboard sharing endpoints
- **2.1.0** (2024-09-01): Added composite alert rules
