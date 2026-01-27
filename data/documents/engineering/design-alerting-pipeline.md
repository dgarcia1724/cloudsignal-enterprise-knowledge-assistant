# Design: Real-time Alerting Pipeline

**Version:** 1.5.0
**Last Updated:** 2024-12-01
**Author:** Marcus Johnson, Staff Engineer
**Status:** Active
**Team:** Backend Platform

## Overview

This document describes the architecture of CloudSignal's real-time alerting pipeline, which processes millions of metrics per minute and evaluates alert rules with sub-second latency.

## System Goals

1. **Low Latency:** Alert evaluation within 5 seconds of metric arrival
2. **High Throughput:** Process 10M+ metrics per minute
3. **Reliability:** 99.99% uptime for alert delivery
4. **Flexibility:** Support complex multi-condition alert rules

## Architecture

### Data Flow

```
Metrics     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
Agents  ───►│   Kafka     │────►│   Flink     │────►│  Alert      │
            │   Ingest    │     │   Processor │     │  Dispatcher │
            └─────────────┘     └──────┬──────┘     └──────┬──────┘
                                       │                    │
                                       ▼                    ▼
                                ┌─────────────┐     ┌─────────────┐
                                │ TimescaleDB │     │ Notification│
                                │  (metrics)  │     │  Services   │
                                └─────────────┘     └─────────────┘
```

### Components

#### 1. Kafka Ingestion Layer

- **Topic:** `metrics.ingest.v1`
- **Partitions:** 64 (by customer_id hash)
- **Retention:** 24 hours
- **Throughput:** 500K messages/second peak

Message schema:
```json
{
  "customer_id": "cust_abc123",
  "metric_name": "cpu.usage",
  "value": 85.5,
  "timestamp": 1704067200,
  "tags": {
    "host": "prod-web-01",
    "region": "us-east-1"
  }
}
```

#### 2. Flink Stream Processor

The Flink job performs:
- Metric aggregation (avg, max, min, p95 over windows)
- Alert rule evaluation
- State management for multi-condition rules

```java
// Simplified rule evaluation
DataStream<Alert> alerts = metrics
    .keyBy(m -> m.getCustomerId() + m.getRuleId())
    .window(TumblingEventTimeWindows.of(Time.seconds(60)))
    .aggregate(new MetricAggregator())
    .filter(agg -> agg.getValue() > agg.getThreshold())
    .map(this::createAlert);
```

#### 3. Alert Rule Types

| Rule Type | Description | Example |
|-----------|-------------|---------|
| Threshold | Single metric crosses value | CPU > 90% |
| Anomaly | Deviation from baseline | 3 std dev from mean |
| Composite | Multiple conditions | CPU > 80% AND Memory > 70% |
| Rate | Change over time | Error rate +50% in 5 min |

#### 4. Alert Dispatcher

Routes alerts to notification channels:
- **Slack:** Webhook integration
- **PagerDuty:** Events API v2
- **Email:** SendGrid
- **Webhook:** Customer-defined endpoints

## Alert Deduplication

Prevents alert storms using:

```python
class AlertDeduplicator:
    def should_send(self, alert: Alert) -> bool:
        key = f"{alert.customer_id}:{alert.rule_id}:{alert.fingerprint}"
        last_sent = redis.get(key)

        if not last_sent:
            redis.setex(key, DEDUP_WINDOW_SECONDS, now())
            return True

        if now() - last_sent > MIN_INTERVAL_SECONDS:
            redis.setex(key, DEDUP_WINDOW_SECONDS, now())
            return True

        return False
```

## Scaling Considerations

### Current Capacity

| Component | Instances | Capacity |
|-----------|-----------|----------|
| Kafka Brokers | 12 | 500K msg/s |
| Flink TaskManagers | 24 | 10M metrics/min |
| Alert Dispatcher | 8 | 50K alerts/min |

### Auto-scaling Triggers

- Kafka consumer lag > 10,000 messages
- Flink backpressure > 50%
- Alert queue depth > 1,000

## Failure Handling

### Kafka Consumer Failures

- Auto-restart with exponential backoff
- Reprocess from last committed offset
- Dead letter queue for poison messages

### Flink Checkpointing

- Checkpoint interval: 30 seconds
- State backend: RocksDB
- Savepoint on deployment for rollback

### Alert Delivery Failures

- Retry with exponential backoff (3 attempts)
- Fallback to secondary channel
- Alert on delivery failures via internal monitoring

## Monitoring

### Key Metrics

- `alerting.pipeline.latency_p99`: End-to-end latency
- `alerting.rules.evaluated_per_second`: Rule evaluation rate
- `alerting.alerts.sent_total`: Alert delivery count
- `alerting.consumer.lag`: Kafka consumer lag

### Dashboards

- [Alerting Pipeline Overview](https://cloudsignal.io/internal/dashboards/alerting)
- [Flink Job Health](https://cloudsignal.io/internal/dashboards/flink)

## Future Improvements

1. **ML-based Anomaly Detection:** Replace static thresholds with learned baselines
2. **Alert Correlation:** Group related alerts into incidents
3. **Predictive Alerting:** Alert before issues occur based on trends

## References

- [Kafka Configuration Guide](/docs/kafka-config)
- [Flink Deployment Runbook](/docs/flink-runbook)
- [Alert Rule Configuration API](/api/v2/alert-rules)
