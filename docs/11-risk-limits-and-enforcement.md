# Risk Limits, Events, and Enforcement Boundaries

## Purpose

This document explains what the simulation's risk controls report and enforce.

> **Scope:** This repository is an educational trading simulation. It is not connected to an exchange and does not execute real financial trades.

## Configured limits

| Limit | Default | Meaning |
|---|---:|---|
| Maximum position | 1,000 units | Maximum permitted absolute position |
| Maximum position value | 100,000 | Maximum permitted position value |
| Maximum drawdown | 1,000 | Equity drawdown threshold |
| Maximum daily loss | 500 | UTC daily-loss threshold |
| Initial engine equity | 100,000 | Starting simulated account equity |

The engine supports `ENGINE_RISK_MAX_POSITION`, `ENGINE_RISK_MAX_POSITION_VALUE`, `ENGINE_RISK_MAX_DRAWDOWN`, `ENGINE_RISK_MAX_DAILY_LOSS`, and `ENGINE_RISK_INITIAL_EQUITY` overrides.

## Durable risk state

When `ENGINE_RISK_STATE_FILE` is set, the engine stores a versioned snapshot containing net position, average entry price, realized P&L, mark price, peak equity, UTC daily baseline, UTC day, halt flag, and halt reason. The snapshot is replaced through a temporary file and rename. A missing snapshot initializes a new simulation; a malformed, incompatible, or truncated existing snapshot causes startup to fail closed. Do not delete a snapshot to recover from a failed startup: preserve it for investigation.

Docker Compose sets `ENGINE_RISK_STATE_FILE=/var/lib/trading-engine/risk-state.snapshot` and mounts the named volume `trading-engine-risk-state`. Ordinary container replacement/restarts preserve this volume. Deleting the named volume destroys the risk snapshot. Local runs default to `./data/risk-state.snapshot`; keep this path on durable storage.

The persisted state is an atomic single-file snapshot, not a transactional trade ledger. It does not protect against storage-device failure, external edits, or a crash between a successful match and its subsequent snapshot write. The simulation is single-process and must not run two engines against the same state file. For production-grade guarantees, use durable append-only trade records, checksums, locking, fsync/dirsync, and recovery reconciliation.

## Halt and operator-authorized resume

Drawdown and daily-loss halts remain latched across restarts. Recovery in price or UTC date rollover does not clear a halt. The engine remains alive for observability but stops admitting further matching once it observes the halt.

A local operator may explicitly authorize resume at startup by setting `ENGINE_RISK_RESUME_AUTHORIZATION=I_ACKNOWLEDGE_RISK_HALT`. This clears the persisted halt flag, preserves the recovered position and P&L, and resets the peak-equity and current UTC daily-loss references to current equity. This is an explicit risk-baseline reset; preserve incident evidence and review the decision before setting the variable. The variable is an operator acknowledgement, **not an authentication system**. Do not expose it through an unauthenticated API or set it in the default Compose environment. Unset it for normal restart behavior.

## Operational response

1. Do not restart merely to clear a halt.
2. Preserve logs, the snapshot, effective limits, halt reason, equity, drawdown, and daily loss.
3. Investigate trade sequence, mark prices, and accounting before authorizing resume.
4. If the snapshot is corrupt or incompatible, stop and preserve it; do not silently replace it.
5. Verify readiness, effective configuration, restored position, and halt state after restart.

## Runtime verification

```bash
docker compose ps
docker compose logs --since=5m engine
docker compose exec engine sh -lc 'ls -l /var/lib/trading-engine && cat /var/lib/trading-engine/risk-state.snapshot'
```

Do not use `docker compose down -v` when you intend to preserve risk state.

## Acceptance criteria

- Position, P&L, peak equity, UTC daily baseline, and halt state restore across restart.
- Invalid or incompatible snapshots prevent engine startup.
- State updates use atomic replacement and storage failures fail closed.
- Halt remains latched after restart unless the explicit local operator acknowledgement is supplied.
- Resume preserves accounting state and re-evaluates active risk limits.
- Docker Compose uses persistent storage for the snapshot.
