# Authentication API Documentation

**Version:** 1.2.0
**Last Updated:** 2024-10-20
**Status:** Active
**Base URL:** `https://auth.cloudsignal.io`

## Overview

CloudSignal uses OAuth 2.0 for user authentication and API keys for service-to-service communication. This document covers both authentication methods.

## OAuth 2.0 Flow

### Authorization Code Flow (Web Apps)

1. Redirect user to authorization endpoint:

```
GET https://auth.cloudsignal.io/oauth/authorize
  ?client_id=YOUR_CLIENT_ID
  &redirect_uri=https://yourapp.com/callback
  &response_type=code
  &scope=read:metrics write:alerts
  &state=random_state_string
```

2. User authenticates and authorizes your app

3. CloudSignal redirects back with authorization code:

```
https://yourapp.com/callback?code=AUTH_CODE&state=random_state_string
```

4. Exchange code for tokens:

```http
POST https://auth.cloudsignal.io/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=AUTH_CODE
&redirect_uri=https://yourapp.com/callback
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read:metrics write:alerts"
}
```

### Refresh Token Flow

```http
POST https://auth.cloudsignal.io/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=dGhpcyBpcyBhIHJlZnJl...
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
```

## API Keys

### Key Types

| Type | Prefix | Use Case |
|------|--------|----------|
| Live | `cs_live_` | Production API access |
| Test | `cs_test_` | Development and testing |
| Admin | `cs_admin_` | Administrative operations |

### Creating API Keys

```http
POST https://api.cloudsignal.io/v2/api-keys
Authorization: Bearer USER_ACCESS_TOKEN
Content-Type: application/json

{
  "name": "Production Metrics Ingestion",
  "permissions": ["metrics:write", "alerts:read"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

Response:
```json
{
  "id": "key_abc123",
  "key": "cs_live_abc123def456...",
  "name": "Production Metrics Ingestion",
  "permissions": ["metrics:write", "alerts:read"],
  "created_at": "2024-01-15T10:00:00Z",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Note:** The full API key is only shown once. Store it securely.

### Revoking API Keys

```http
DELETE https://api.cloudsignal.io/v2/api-keys/{key_id}
Authorization: Bearer USER_ACCESS_TOKEN
```

## JWT Token Structure

Access tokens are JWTs with the following claims:

```json
{
  "iss": "https://auth.cloudsignal.io",
  "sub": "user_abc123",
  "aud": "https://api.cloudsignal.io",
  "exp": 1704070800,
  "iat": 1704067200,
  "scope": "read:metrics write:alerts",
  "org_id": "org_xyz789",
  "permissions": ["metrics:read", "metrics:write", "alerts:*"]
}
```

## Scopes and Permissions

| Scope | Permissions Granted |
|-------|-------------------|
| `read:metrics` | View metrics data |
| `write:metrics` | Submit metrics |
| `read:alerts` | View alert rules and history |
| `write:alerts` | Create/modify alert rules |
| `read:dashboards` | View dashboards |
| `write:dashboards` | Create/modify dashboards |
| `admin` | Full administrative access |

## Security Best Practices

1. **Store secrets securely:** Never commit API keys or client secrets to version control
2. **Use environment variables:** Load credentials from environment at runtime
3. **Rotate keys regularly:** Rotate API keys every 90 days
4. **Principle of least privilege:** Request only necessary scopes
5. **Monitor key usage:** Review API key usage in the security dashboard

## Error Codes

| Error | Description | Resolution |
|-------|-------------|------------|
| `invalid_client` | Unknown client_id | Verify client credentials |
| `invalid_grant` | Expired or invalid code | Request new authorization |
| `invalid_scope` | Requested scope not allowed | Check app permissions |
| `access_denied` | User denied authorization | N/A - user choice |

## Rate Limits

Authentication endpoints have separate rate limits:

- `/oauth/authorize`: 100 requests/min per IP
- `/oauth/token`: 20 requests/min per client
- `/api-keys`: 10 requests/min per user
