# Risk-Halt Diagnostics and Trade-History Recovery

**Status as of 2026-10-25:** PRs #161, #162, and #165 are merged. PR #165 (merge commit `be26512`) upgrades the risk snapshot format to version 4 and reconstructs missing halt diagnostics as explicitly labelled recovery-time context when startup restores an already-latched halt. The merged `main` source was clean-built locally and all 16 C++ CTest tests passed; GitHub Actions was reported green. This does not establish that the existing live legacy halt has been restarted or that its runtime diagnostics have been observed. Phase 5.14 remains in progress.

> **Scope:** This is an educational trading simulation, not a live-exchange trading system.

## Merged implementation

- [PR #161 — Persist risk-halt trigger diagnostics across restart](https://github.com/adarsh0707-kumar/Trading-Engine/pull/161) upgrades the risk snapshot to version 3. It persists the original trigger reason, timestamp, equity, drawdown, and daily loss. Version 1 and version 2 snapshots remain loadable.
- [PR #162 — Reconcile gateway trade history from durable engine journal](https://github.com/adarsh0707-kumar/Trading-Engine/pull/162) adds the engine's bounded `TRADE_HISTORY` request/response and lets the Gateway reconcile durable journal history on connect/reconnect while deduplicating live trade events.

## Version 4 recovery-context reconstruction

PR #165 adds a `reconstructed` marker to the persisted diagnostic record and upgrades the snapshot format to version 4. When startup restores a latched halt but no diagnostic record exists, the engine records the halt reason and measurements available at recovery time, marks them as reconstructed, and persists the result. Engine logs identify this origin as `reconstructed_recovery_context` and use `recovery_*` fields rather than `trigger_*` fields.

These reconstructed values are **not** historical trigger-time metrics. They describe the state observed during recovery and must not be presented as the exact equity, drawdown, daily loss, or timestamp at which the original halt occurred. Original trigger diagnostics that were already persisted remain labelled as original trigger data. Snapshot versions 1–3 remain supported; version 4 validates the reconstruction marker and fails closed for invalid metadata.

## Diagnostic semantics and legacy state

Risk-halt diagnostics describe the moment a halt is first triggered; they are not a substitute for current metrics. A live threshold crossing captures and persists the trigger fields. Journal replay can restore a latched halt, but replay must not invent a new trigger timestamp or use current equity as though it were the historical trigger value.

An already-latched halt in a legacy snapshot without diagnostic fields remains latched. With PR #165, the next startup/recovery can persist explicitly marked recovery-time context so logs are not forced to report diagnostics as unavailable. This does not recover the original trigger values from the snapshot or journal. Do not describe recovery-time measurements as historical trigger values, clear the halt, or reset the snapshot/journal to make the diagnostics appear complete.

Snapshot version 3 introduced the diagnostic trigger flag, reason, timestamp in milliseconds, equity, drawdown, and daily loss. Snapshot version 4 adds the reconstruction-origin marker. The loader retains version 1–3 compatibility and rejects malformed diagnostic data or an invalid version-4 reconstruction marker rather than silently accepting it.

## Runtime evidence recorded on 2026-10-23

After PR #162 was deployed from `main` at `bbf84fa`:

- All five Docker Compose services were healthy.
- Gateway readiness reported the engine and analytics dependencies connected.
- `GET /api/v1/trades` returned 23 trades in newest-first order.
- Gateway logs recorded `engine_trade_history_reconciled` with `recordCount: 23` and `outcome: "accepted"`.
- The durable journal hash remained unchanged during deployment verification.

The existing risk snapshot was version 3 and still represented a latched `max_drawdown` halt with default/unavailable diagnostic fields. That is expected for a halt created before its original trigger diagnostics were persisted. This does **not** prove that the live halt can recover missing historical values.

## Isolated restart-persistence regression test recorded on 2026-10-24

The focused test `test_state_restores_position_pnl_and_halt_after_restart` was compiled from a temporary copy of the test source and run by itself against the existing local `libengine_core.a`. The temporary copy used a unique directory under `/tmp` for its snapshot and journal, and its test runner invoked only this regression test.

- Result: **PASS** — output: `Isolated restart-persistence test passed`.
- The test exercised restoring a newly triggered `max_drawdown` halt, its diagnostic reason, positive trigger timestamp, trigger equity and drawdown, and the position/equity state.
- The test also exercised denial of resume without authorization and successful authorization against its own isolated fixture only.
- The repository remained clean at `b647997`; all five Docker Compose services remained healthy after the test.
- Compilation emitted unused-function warnings because the temporary executable intentionally invoked only one test. No test failure occurred.
- This is isolated regression evidence, not a live-volume restart test. It does not recover or validate diagnostics for the pre-existing live halt.



## Isolated gateway and browser WebSocket validation recorded on 2026-10-24

The following tests passed after the local checkout was fast-forwarded to GitHub `main` at `3b40ec4`:

- `gateway-node/tests/websocket-e2e.test.ts`: **PASS** — 1 test, 0 failures, 3 assertions. The isolated test delivered a C++-protocol `TRADE` message to a subscribed WebSocket client.
- `gateway-node/tests/full-stack.integration.test.ts`: **PASS** — 1 test, 0 failures, 11 assertions. The isolated integration path exercised an Engine `TRADE`, analytics update, risk event, and WebSocket consumers.
- `dashboard-react/e2e/websocket-recovery.e2e.ts`: **PASS** — 1 browser test. It simulated a WebSocket drop, observed a replacement subscription, injected mocked `MARKET_DATA`, and verified the displayed price updated after reconnection.

The browser test intercepts the WebSocket and mocks the market/trade HTTP endpoints. These results validate isolated gateway behavior and frontend reconnect handling, not delivery of a live engine or analytics risk event through the running Docker stack. The runtime browser event path remains unverified.

The local runtime's read-only health checks continued to return HTTP 200 and all five containers were healthy. The live analytics response still reported `riskStatus: "unknown"` with a stale timestamp, while engine logs continued to report unavailable trigger diagnostics for the pre-existing `max_drawdown` halt. Do not infer that either live-state limitation was resolved by these isolated tests.

## Safe validation procedure

Run the risk tests against the repository's test harness and disposable temporary state only. Do not point a test at the live Docker volume or its journal.

1. Confirm the repository is on the expected `main` commit and inspect the C++ test target names.
2. Run the focused risk-guard test target, including the regression test that journal replay crossing a risk threshold restores the halt without fabricating live diagnostics.
3. The isolated restart-persistence regression described above has passed using a temporary test-source copy and temporary snapshot/journal paths. Keep this distinct from live-state validation.
4. Verify legacy version 1 and version 2 snapshot compatibility and version 3 malformed-diagnostic rejection where covered by tests.
5. Record exact commands and pass/fail output for each remaining check. If coverage is missing or fails, report that before making code changes.

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
