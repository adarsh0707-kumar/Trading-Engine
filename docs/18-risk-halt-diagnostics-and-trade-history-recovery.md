# Risk-Halt Diagnostics and Trade-History Recovery

**Status as of 2026-10-23:** PRs #161 and #162 are merged. PR #162 is deployed in the local Docker runtime and its trade-history reconciliation path has been observed working. Focused isolated validation of risk-halt diagnostic persistence across restart is still pending. Phase 5.14 remains in progress.

> **Scope:** This is an educational trading simulation, not a live-exchange trading system.

## Merged implementation

- [PR #161 — Persist risk-halt trigger diagnostics across restart](https://github.com/adarsh0707-kumar/Trading-Engine/pull/161) upgrades the risk snapshot to version 3. It persists the original trigger reason, timestamp, equity, drawdown, and daily loss. Version 1 and version 2 snapshots remain loadable.
- [PR #162 — Reconcile gateway trade history from durable engine journal](https://github.com/adarsh0707-kumar/Trading-Engine/pull/162) adds the engine's bounded `TRADE_HISTORY` request/response and lets the Gateway reconcile durable journal history on connect/reconnect while deduplicating live trade events.

## Diagnostic semantics and legacy state

Risk-halt diagnostics describe the moment a halt is first triggered; they are not a substitute for current metrics. A live threshold crossing captures and persists the trigger fields. Journal replay can restore a latched halt, but replay must not invent a new trigger timestamp or use current equity as though it were the historical trigger value.

An already-latched halt in a legacy snapshot without diagnostic fields remains halted with diagnostics explicitly unavailable. The original trigger values cannot reliably be reconstructed from the snapshot and journal alone. Do not backfill them with current measurements, clear the halt, or reset the snapshot/journal to make the diagnostics appear complete.

Snapshot version 3 includes the existing accounting and journal-sequence fields followed by the diagnostic trigger flag, reason, timestamp in milliseconds, equity, drawdown, and daily loss. The loader validates diagnostic values and rejects malformed version 3 diagnostic data rather than silently accepting it.

## Runtime evidence recorded on 2026-10-23

After PR #162 was deployed from `main` at `bbf84fa`:

- All five Docker Compose services were healthy.
- Gateway readiness reported the engine and analytics dependencies connected.
- `GET /api/v1/trades` returned 23 trades in newest-first order.
- Gateway logs recorded `engine_trade_history_reconciled` with `recordCount: 23` and `outcome: "accepted"`.
- The durable journal hash remained unchanged during deployment verification.

The existing risk snapshot was version 3 and still represented a latched `max_drawdown` halt with default/unavailable diagnostic fields. That is expected for a halt created before its original trigger diagnostics were persisted. This does **not** prove that a newly triggered halt's diagnostics survive restart; that behavior needs isolated test evidence.

## Safe validation procedure

Run the risk tests against the repository's test harness and disposable temporary state only. Do not point a test at the live Docker volume or its journal.

1. Confirm the repository is on the expected `main` commit and inspect the C++ test target names.
2. Run the focused risk-guard test target, including the regression test that journal replay crossing a risk threshold restores the halt without fabricating live diagnostics.
3. Run the test that triggers a new max-drawdown halt, destroys/recreates only its temporary `RiskGuard` instance, and asserts that the original reason, positive timestamp, trigger equity, and drawdown are restored.
4. Verify legacy version 1 and version 2 snapshot compatibility and version 3 malformed-diagnostic rejection where covered by tests.
5. Record the exact test command, target, and pass/fail output. If coverage is missing or fails, report that before making code changes.

Example read-only repository inspection from the project root:

```bash
git status -sb
git rev-parse --short HEAD
rg -n "test_replay_that_crosses_risk_threshold_restores_halt_without_live_diagnostics|halt_diagnostics|risk_guard" engine-cpp
```

Use the project's existing CMake/CTest configuration to determine the exact focused test command rather than guessing a target name.

## Operational safety rules

- Preserve the live `max_drawdown` halt and its original snapshot/journal.
- Do not set `ENGINE_RISK_RESUME_AUTHORIZATION`, change risk limits, submit synthetic trades to the live stack, or delete/reset any persistent volume.
- Do not delete the active snapshot, temporary snapshots, or trade journal. Keep the existing forensic backups.
- A healthy service, successful CI, or an available `/api/v1/trades` response is not proof of risk-diagnostic persistence across restart.
- Keep the trade-history reconciliation and risk-diagnostics validation as separate checks so each result is attributable.

See [Risk Limits, Events, and Enforcement](11-risk-limits-and-enforcement.md) for durable-state and operator-resume policy, and [Phase Roadmap](05-roadmap-and-phases.md) for overall milestone status.
