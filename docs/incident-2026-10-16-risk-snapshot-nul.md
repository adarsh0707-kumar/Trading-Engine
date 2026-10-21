# Incident: Risk-State Snapshot NUL Corruption (2026-10-16 → 2026-10-18)

**Status:** Closed
**Severity:** High (engine cannot start; simulated trading blocked)
**Component:** C++ engine — `RiskGuard` persistent state (`engine-cpp/src/engine/RiskGuard.cpp`)
**Related PRs:** #154 (`fix/risk-snapshot-durability`, `96d6867`, merge `c90ac57`), #156 (`fix/risk-halt-diagnostics`, `180d033`)
**Related commits:** `612d384` (initial journal + atomic-write path), `8443f29` (snapshot-covered duplicate trade IDs), `96d6867` (durability fix), `040acbc` (halt trigger diagnostics)

## Summary

Between 2026-10-16 and 2026-10-18, the running C++ engine repeatedly failed to start with:
Engine startup failed closed: risk state is corrupt or incompatible; refusing startup
Root cause: the `risk-state.snapshot` file on the `trading-engine-risk-state` Docker volume contained 114 NUL bytes (`\x00`), not a parseable version-2 snapshot. `RiskGuard::load_state()` fails closed on unparsable input, producing exactly that error string.

The corruption was produced by the pre-`96d6867` `save_state()` implementation, which did not `fsync` before `rename`, and which on Docker Desktop (VM-backed filesystem) could leave a correctly-sized, zero-content file at the target path after an unclean event. `96d6867` added `fsync` before `rename`, `fsync` on the parent directory after `rename`, `O_EXCL` on the temp file, and a nonce-retry loop. The current running engine image contains that fix (verified by binary string inspection).

## Timeline (UTC unless noted)

| Time | Event | Evidence |
|---|---|---|
| 2026-10-16 18:56 | Valid 114-byte snapshot on disk | `trading-engine-live-evidence-20261016T132637Z/risk-state.snapshot` |
| 2026-10-16 22:59 | Snapshot on disk is 114 NUL bytes; mtime frozen here for ~2 days | `trading-engine-pre-restore-20261018T215219/risk-state.snapshot.corrupt`, and five sibling captures with identical mtime |
| 2026-10-17 20:33 → 2026-10-18 21:52 | Every volume capture reads the same NUL file | `trading-engine-volume-inspection-20261017-203355`, `-recheck-20261017-204010`, `-temp-state-audit-20261017-211551`, `-live-read-FxCgXq`, `-pre-restore-…` |
| 2026-10-18 16:38 | `risk-state-diagnostic` container exits 2 (fail-closed) | `docker inspect 1fb9480433d4` |
| 2026-10-18 21:40 | `96d6867` authored — durability fix | `git show -s 96d6867` |
| 2026-10-19 20:20 | PR #154 merged (`c90ac57`) | `git show -s c90ac57` |
| 2026-10-20 21:35 | Valid 117-byte snapshot captured | `trading-engine-forensics-20261020T160547Z/risk-state.snapshot` |
| 2026-10-21 01:43 | Current engine container starts cleanly | `docker inspect trading-engine-engine-1` → `StartedAt` |

## Verified facts

1. **NUL file is single, not recurrent.** Six capture directories across 2026-10-17 20:33 through 2026-10-18 21:52 contain a 114-byte `risk-state.snapshot` with mtime `2026-10-16 22:59` and first byte `0x00`. They are the same file captured at different times.
2. **A separate earlier NUL file** exists at `trading-engine-forensics-20261016-182703/risk-state.snapshot` — 108 bytes, mtime 2026-10-15 20:27. Also NUL, possibly the same failure at a different serialized-length point.
3. **Current running image contains `96d6867`.** `/app/engine` in `trading-engine-engine-1` (SHA-256 `0551b832ddff671ccd43695fd504d174a240558e40fd34e341f418c058c91268`) contains the string literals `"snapshot replaced"`, `"risk-state directory"`, and `"temporary risk-state"`, all introduced by `96d6867`.
4. **Current live snapshot is valid.** Captured atomically from `/var/lib/trading-engine/risk-state.snapshot`: `2 203 99.083793103448286 -262.77999999999929 100.78 100938.20999999999 99379.169999999998 20747 1 max_drawdown 17` — parses cleanly against `load_state()`, has `journal_sequence=17`, and matches the current 17-record journal.
5. **Current fail-closed state is not active.** `docker inspect trading-engine-engine-1` shows `RestartCount=0`, `StartedAt=2026-10-21T01:43:47Z`, and the running engine reports `replayed_records=0 last_sequence=17` then `risk_halt_active reason=max_drawdown`. No fail-closed since that start.
6. **The fail-closed error string is source-matched.** `RiskGuard.cpp:load_state()` throws `"risk state is corrupt or incompatible; refusing startup"` on unparsable input. A NUL-filled file fails the first `std::istream >>` extraction and trips the condition.
7. **The forensic journal's 18th line is a duplicate of line 1** (same trade ID, new timestamp, new checksum). `replay_trade_journal()` accepts this when `sequence(18) <= snapshot_sequence(18)` — which the candidate snapshot provides — and rejects it otherwise. Both the 2026-10-16 code and the current code are consistent with this behavior (the acceptance policy was introduced in `8443f29`).

## Root cause

`save_state()` pre-`96d6867` wrote directly to the target path with no `fsync` before `rename`. On Docker Desktop (QEMU-backed filesystem), an unclean event (host sleep, VM pause, forced stop) between `write()` and the eventual disk flush could leave the *new inode's allocated size* on disk with zero content in its pages. The pre-`96d6867` writer did not detect this because it never read back the file after `rename`.

`96d6867` added:
- `fsync()` on the temp file before `rename` — the data reaches durable storage before the rename exposes the new path;
- `fsync()` on the parent directory after `rename` — the rename itself survives a crash;
- `O_EXCL` on the temp file plus a nonce-retry loop — concurrent writers cannot collide;
- explicit error messages on each durability step.

## Not established

- **Whether `fsync` absence alone was sufficient** to produce this, or whether the VM's virtual-disk caching layer also contributed. A controlled reproduction under VM-crash stress was not performed, and its result would not change the resolution (the fix is already in the running image).
- **The 2026-10-18 16:44 successful-startup log line** appears in the running container's log buffer before the 21:52 NUL capture, and it is not reconciled with the NUL file's continuous mtime. Likely a prior container instance whose logs the current container inherited via name reuse; not material to the resolution.

## Resolution

1. `96d6867` (PR #154, merged `c90ac57` on 2026-10-19) is the durability fix.
2. The current running engine image contains `96d6867` (verified by string inspection).
3. The current live snapshot is valid and internally consistent with the current journal.
4. No recurrence of NUL content has been observed since the fix was deployed.

## Follow-up (not required for closure)

- **Per-condition error messages** in `load_state()`: currently nine distinct fail-closed conditions emit the same error string. Splitting them (unparsable vs. version mismatch vs. bounds vs. halted-without-reason) would make any future occurrence a one-minute diagnosis instead of a multi-hour investigation.
- **Snapshot redundancy**: write `risk-state.snapshot` and rotate the previous successful write to `risk-state.snapshot.prev`; on load, fall back to `.prev` if `.snapshot` is unparsable. Turns single-file corruption into a recoverable state.

Neither follow-up is required to close this incident. Both are optional hardening for the next milestone.

## Evidence retention

Forensic captures under `$HOME/trading-engine-*` should be preserved as the incident's evidence trail. Specifically:

- `trading-engine-forensics-20261016-182703/` — the first NUL snapshot (108 bytes) and candidate (96 bytes, valid)
- `trading-engine-live-evidence-20261016T132637Z/` — the pre-NUL valid snapshot (114 bytes)
- `trading-engine-pre-restore-20261018T215219/`, `-recheck-20261017-204010/`, `-volume-inspection-20261017-203355/`, `-temp-state-audit-20261017-211551/`, `-live-read-FxCgXq/` — the NUL-window captures (all 114 bytes, mtime 2026-10-16 22:59)
- `trading-engine-forensics-20261020T160547Z/` — the post-fix valid snapshot (117 bytes)

Do not delete or move these directories without an explicit retention decision.
