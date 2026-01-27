# TypeScript Best Practices Guide

**Version:** 1.0.0
**Last Updated:** 2024-11-30
**Owner:** Frontend & UI Team
**Status:** Active

## Overview

This guide defines TypeScript and React coding standards for CloudSignal's frontend applications. Following these conventions ensures consistency across our dashboard and UI components.

## TypeScript Configuration

Use strict TypeScript settings:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `DashboardWidget.tsx` |
| Hooks | camelCase with `use` prefix | `useDashboard.ts` |
| Types/Interfaces | PascalCase | `DashboardConfig` |
| Constants | UPPER_SNAKE_CASE | `MAX_WIDGETS` |
| Functions | camelCase | `fetchMetrics()` |
| Files | kebab-case | `dashboard-widget.tsx` |

## Component Structure

Follow this order within component files:

```typescript
// 1. Imports
import { useState, useEffect } from 'react';
import { Card, Button } from '@/components/ui';
import { useMetrics } from '@/hooks/useMetrics';
import type { Metric } from '@/types';

// 2. Types
interface DashboardWidgetProps {
  metricId: string;
  refreshInterval?: number;
  onError?: (error: Error) => void;
}

// 3. Constants
const DEFAULT_REFRESH_INTERVAL = 30000;

// 4. Component
export function DashboardWidget({
  metricId,
  refreshInterval = DEFAULT_REFRESH_INTERVAL,
  onError,
}: DashboardWidgetProps) {
  // 4a. Hooks
  const [isLoading, setIsLoading] = useState(true);
  const { data, error } = useMetrics(metricId);

  // 4b. Effects
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // 4c. Handlers
  const handleRefresh = () => {
    setIsLoading(true);
    // refresh logic
  };

  // 4d. Render
  if (isLoading) {
    return <Card>Loading...</Card>;
  }

  return (
    <Card>
      <h3>{data?.name}</h3>
      <p>{data?.value}</p>
      <Button onClick={handleRefresh}>Refresh</Button>
    </Card>
  );
}
```

## Type Definitions

### Prefer Interfaces for Objects

```typescript
// Good - use interface for object shapes
interface User {
  id: string;
  name: string;
  email: string;
}

// Use type for unions, primitives, tuples
type AlertSeverity = 'critical' | 'warning' | 'info';
type Coordinates = [number, number];
```

### Avoid `any`

```typescript
// Bad
function processData(data: any) { ... }

// Good - use unknown and type guards
function processData(data: unknown) {
  if (isMetricData(data)) {
    // data is now typed as MetricData
  }
}

// Type guard
function isMetricData(data: unknown): data is MetricData {
  return (
    typeof data === 'object' &&
    data !== null &&
    'value' in data &&
    'timestamp' in data
  );
}
```

### Use Generics Appropriately

```typescript
// Good - generic hook for data fetching
function useFetch<T>(url: string): {
  data: T | null;
  loading: boolean;
  error: Error | null;
} {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  // ...
  return { data, loading, error };
}

// Usage
const { data } = useFetch<Metric[]>('/api/metrics');
```

## React Best Practices

### Prefer Functional Components

```typescript
// Good - functional component with hooks
export function MetricCard({ metric }: { metric: Metric }) {
  const [expanded, setExpanded] = useState(false);
  return <div>...</div>;
}

// Avoid class components for new code
```

### Memoization

Use `useMemo` and `useCallback` appropriately:

```typescript
// Good - expensive computation
const sortedMetrics = useMemo(
  () => metrics.sort((a, b) => b.value - a.value),
  [metrics]
);

// Good - callback passed to child
const handleClick = useCallback(
  (id: string) => {
    selectMetric(id);
  },
  [selectMetric]
);

// Bad - unnecessary memoization
const name = useMemo(() => user.name, [user.name]); // Just use user.name
```

### Custom Hooks

Extract reusable logic into custom hooks:

```typescript
// hooks/useDebounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage
const debouncedSearch = useDebounce(searchTerm, 300);
```

## Error Handling

```typescript
// Use Error Boundaries for component errors
import { ErrorBoundary } from '@/components/ErrorBoundary';

function Dashboard() {
  return (
    <ErrorBoundary fallback={<ErrorFallback />}>
      <DashboardContent />
    </ErrorBoundary>
  );
}

// Handle async errors explicitly
async function fetchData() {
  try {
    const response = await api.get('/metrics');
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      // Handle API-specific errors
    }
    throw error;
  }
}
```

## Testing

```typescript
// Component testing with React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';

describe('MetricCard', () => {
  it('displays metric value', () => {
    const metric = { id: '1', name: 'CPU', value: 85 };
    render(<MetricCard metric={metric} />);
    expect(screen.getByText('85')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = jest.fn();
    render(<MetricCard metric={metric} onClick={onClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledWith('1');
  });
});
```

## Formatting & Linting

```bash
# Run Prettier
pnpm format

# Run ESLint
pnpm lint

# Run type checking
pnpm typecheck
```

## Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [CloudSignal Component Library](/docs/components)
