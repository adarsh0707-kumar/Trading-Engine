# Operational Alerting

Phase 4.9.5 adds Prometheus alert rules for gateway operational failures.

## Prometheus integration

The Prometheus configuration in `infra/prometheus/prometheus.yml` now:

- evaluates alert rules every 5 seconds;
- loads `/etc/prometheus/alerts.yml`;
- scrapes the Gateway `/metrics` endpoint on `gateway:8080`;
- continues scraping Python Analytics on `analytics:9101`.

The alert file is mounted into the Prometheus container at `/etc/prometheus/alerts.yml` by the deployment environment.

## Alert policy

### Critical dependency availability

| Alert | Condition | For |
| --- | --- | --- |
| `GatewayNotReady` | `gateway_ready == 0` | 1 minute |
| `GatewayEngineDisconnected` | `gateway_engine_connected == 0` | 1 minute |
| `GatewayAnalyticsDisconnected` | `gateway_analytics_connected == 0` | 1 minute |

These alerts represent sustained dependency or gateway readiness loss rather than a single transient event.

### Warning operational failures

The following alerts use the existing monotonic failure counters and fire when at least one failure is observed in the previous five minutes:

- `GatewayEngineLivenessFailures`
- `GatewayEngineConnectionFailures`
- `GatewayEngineProtocolFailures`
- `GatewayAnalyticsQueueOverflow`
- `GatewayAnalyticsSendFailures`

`GatewayHttp5xxRate` is a warning alert when the Gateway returns more than 0.1 HTTP 5xx responses per second for two consecutive minutes.

## Notification routing

Phase 4.9.5 defines Prometheus alert conditions and severity metadata. It does not hard-code an Alertmanager endpoint, notification channel, paging service, email destination, or webhook credential.

A deployment can connect these rules to Alertmanager or another Prometheus-compatible notification path without changing Gateway application code.

## Design constraints

- Alert expressions use existing Gateway metrics; no duplicate failure counters are introduced.
- No request IDs, event IDs, client addresses, payloads, or other high-cardinality values are used as alert labels.
- Alerts describe observable failure conditions and do not alter Gateway request, engine, analytics, or WebSocket behavior.
- Transient dependency changes are separated from sustained readiness loss using `for` durations where appropriate.
