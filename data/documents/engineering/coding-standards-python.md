# Python Style Guide

**Version:** 2.0.0
**Last Updated:** 2025-01-10
**Owner:** Backend Platform Team
**Status:** Active

## Overview

This document defines the Python coding standards for all CloudSignal engineering teams. Following these guidelines ensures consistency, maintainability, and quality across our codebase.

## Code Formatting

### General Rules

- **Line Length:** Maximum 100 characters
- **Indentation:** 4 spaces (no tabs)
- **Encoding:** UTF-8 for all Python files
- **Formatter:** Black with `--line-length 100`

### Imports

Organize imports in the following order with blank lines between groups:

```python
# Standard library
import os
import sys
from typing import List, Optional, Dict

# Third-party packages
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx

# Local application imports
from app.core.config import settings
from app.services.metrics import MetricsService
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `AlertConfiguration` |
| Functions | snake_case | `process_metrics()` |
| Variables | snake_case | `alert_threshold` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Private | Leading underscore | `_internal_helper()` |

## Type Hints

Type hints are **required** for all function signatures:

```python
# Good
def calculate_alert_threshold(
    metrics: List[float],
    sensitivity: float = 1.0
) -> Optional[float]:
    """Calculate dynamic alert threshold based on metrics."""
    if not metrics:
        return None
    return sum(metrics) / len(metrics) * sensitivity

# Bad - missing type hints
def calculate_alert_threshold(metrics, sensitivity=1.0):
    return sum(metrics) / len(metrics) * sensitivity
```

## Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def send_alert(
    channel: str,
    message: str,
    severity: AlertSeverity,
    metadata: Optional[Dict[str, Any]] = None
) -> AlertResponse:
    """Send an alert notification to the specified channel.

    Args:
        channel: The notification channel (slack, pagerduty, email).
        message: The alert message content.
        severity: Alert severity level (critical, warning, info).
        metadata: Optional additional context for the alert.

    Returns:
        AlertResponse containing delivery status and tracking ID.

    Raises:
        ChannelNotFoundError: If the specified channel doesn't exist.
        RateLimitExceeded: If alert rate limit is exceeded.
    """
    ...
```

## Async/Await Best Practices

CloudSignal's backend is async-first. Follow these patterns:

```python
# Use async for I/O operations
async def fetch_metrics(client_id: str) -> List[Metric]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{METRICS_URL}/{client_id}")
        return [Metric(**m) for m in response.json()]

# Use asyncio.gather for parallel operations
async def fetch_all_dashboards(user_id: str) -> List[Dashboard]:
    dashboard_ids = await get_user_dashboard_ids(user_id)
    dashboards = await asyncio.gather(
        *[fetch_dashboard(did) for did in dashboard_ids]
    )
    return dashboards
```

## Error Handling

```python
# Use specific exceptions
class MetricProcessingError(CloudSignalError):
    """Raised when metric processing fails."""
    pass

# Provide context in exceptions
try:
    result = await process_metric_batch(metrics)
except ValidationError as e:
    raise MetricProcessingError(
        f"Invalid metric format in batch: {e.message}",
        metric_ids=[m.id for m in metrics]
    ) from e
```

## Testing Requirements

- Minimum 80% code coverage for new code
- Use pytest with async support
- Mock external services in unit tests

```python
@pytest.mark.asyncio
async def test_alert_threshold_calculation():
    metrics = [10.0, 20.0, 30.0]
    result = await calculate_alert_threshold(metrics)
    assert result == 20.0
```

## Linting and Quality Tools

Run these before committing:

```bash
# Format code
black --line-length 100 .

# Lint code
ruff check .

# Type checking
mypy --strict app/
```

## Resources

- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
- [Black Formatter](https://black.readthedocs.io/)
- [CloudSignal Backend Patterns](/docs/patterns)
