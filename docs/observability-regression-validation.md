# Observability Regression & Validation

Phase 4.9.6 is the final validation milestone for the Phase 4.9 observability work.

## Automated validation

The repository test workflow validates four areas:

- C++ Engine Debug and Release builds with the full CTest suite.
- Python Analytics tests against PostgreSQL 17.
- Gateway build, security regression tests, and the full Bun test suite.
- Prometheus configuration and alert-rule syntax with a pinned Prometheus toolchain.

The Prometheus validation mounts `infra/prometheus/` as the Prometheus configuration directory so `prometheus.yml` and `alerts.yml` are validated together.

## Observability regression scope

The existing Gateway tests cover:

- structured operational logging;
- Engine and Analytics state transitions;
- request/event correlation;
- liveness and readiness behavior;
- rate-limit boundaries;
- metrics emission;
- WebSocket event publication;
- safe public error exposure.

The Prometheus validation additionally ensures the operational alerting configuration remains syntactically valid after changes.

## Release gate

Phase 4.9 is complete only when the complete CI workflow passes, including both Engine build types, Analytics, Gateway, security regression, and Prometheus configuration/rule validation.
