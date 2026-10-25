# Production Deployment and Rollback: Risk-Halt Recovery

**Status:** Prepared runbook; deployment not performed.  
**Scope:** Deploy the engine build containing version-4 risk snapshots and reconstructed halt diagnostics.  
**Safety invariant:** The persisted risk halt remains active. Never set `ENGINE_RISK_RESUME_AUTHORIZATION`, clear the halt, delete state files, or run a reset against the live volume as part of this procedure.

## Current verified baseline

The preflight captured on 2026-10-25 reported:

- Git `main` and `origin/main` at `b12d1f448d7faffa28a9732338562895c8a1f08d`.
- `engine-cpp/src/engine/RiskGuard.cpp` declares `STATE_VERSION = 4`.
- Locally built image tag `trading-engine-engine:latest`, image ID `sha256:c40492ad8dfb927f5882ebe22afd301fabd3fbc06f9dfd0eef1daaaa90253a79`; `/app/engine` SHA-256 `1e3c86bf2a7e0f9eb27515811a4713f84dde245bfbbdd11ad0b0795cce55a784`.
- Running engine container was still on image ID `sha256:a4ad2102e723506951857ef82ba03a027e64d12cd22bc0b3beae1627b1c7cb58`, running with restart count 0.
- Live snapshot was version 3; logs reported `trigger_diagnostics=unavailable`, reason `max_drawdown`, current equity approximately 99824.17 and drawdown approximately 1150.14 against a 1000 limit.
- Isolated tests passed for legacy snapshot recovery and a second startup from the version-4 snapshot. The reconstructed values are recovery-time context, not historical trigger-time metrics.

These are dated observations, not a guarantee that the live environment has not changed. Re-run all preflight checks immediately before a maintenance window.

## Gate 0 — prerequisites

- Announce a maintenance window and confirm no operator/client is submitting requests to the engine.
- Confirm the repository worktree is clean and `main` is at the reviewed commit.
- Confirm the intended local image ID and binary hash before touching the running container.
- Keep the existing engine halted for risk purposes. This deployment does not authorize trading to resume.
- Do not use `docker compose down`, remove named volumes, prune Docker, or rebuild other services as part of this engine-only rollout.

If any assumption is unclear, stop before the maintenance window.

## Gate 1 — pre-stop evidence

From the repository directory, record the current container and image identities:

```bash
cd "/run/media/mahakal1008/Adarsh/Projects/Trading-Engine" || exit 1

git status -sb
git rev-parse HEAD
git rev-parse origin/main
docker image inspect trading-engine-engine:latest --format 'ImageID={{.Id}} Created={{.Created}}'
docker compose ps
ENGINE_ID="$(docker compose ps -q engine)"
[ -n "$ENGINE_ID" ] || { echo "Engine container not found; stop."; exit 1; }
docker inspect "$ENGINE_ID" --format 'Name={{.Name}} Status={{.State.Status}} RestartCount={{.RestartCount}} ImageID={{.Image}} StartedAt={{.State.StartedAt}}'
docker inspect "$ENGINE_ID" --format '{{range .Mounts}}{{if eq .Destination "/var/lib/trading-engine"}}Type={{.Type}} Name={{.Name}} Source={{.Source}} Destination={{.Destination}}{{end}}{{end}}'
docker logs --tail 100 "$ENGINE_ID" 2>&1
```

Record output outside the repository. Confirm the mount source is the expected `trading-engine_trading-engine-risk-state` volume. If the container, volume, source commit, image ID, or halt reason differs unexpectedly, stop and investigate.

## Gate 2 — stop cleanly and capture a consistent backup

The next operation interrupts the engine. Run only during the approved maintenance window.

1. Stop only the engine service and allow SIGTERM/graceful shutdown:

```bash
docker compose stop -t 30 engine
```

2. Confirm it is stopped before copying. Do not proceed if it is still running:

```bash
ENGINE_ID="$(docker compose ps -aq engine)"
docker inspect "$ENGINE_ID" --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} FinishedAt={{.State.FinishedAt}}'
```

3. Copy the **entire** risk-state directory, including the snapshot, journal, and all temporary snapshot files. Derive the source from the inspected volume mount; do not assume a different volume name. With the currently verified mount, the example is:

```bash
set -eu
SOURCE="/var/lib/docker/volumes/trading-engine_trading-engine-risk-state/_data"
BACKUP="$HOME/trading-engine-predeploy-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -m 700 "$BACKUP"
cp -a "$SOURCE/." "$BACKUP/"
chmod -R go-rwx "$BACKUP"

echo "Backup directory: $BACKUP"
find "$BACKUP" -maxdepth 1 -type f -exec ls -ln {} \; -exec sha256sum {} \;
```

4. Verify that the snapshot and journal exist in the backup and that the hashes are recorded. Preserve the backup untouched. If copy or verification fails, **do not deploy**; start the existing engine only if operationally necessary and investigate the failed backup.

The source path above is host-specific. Use the actual mount source from Gate 1 if it differs.

## Gate 3 — deploy the engine only

Do not execute this gate until the backup is verified and the maintenance window is approved.

1. Reconfirm that the local target image ID is the reviewed image ID.
2. Reconfirm the engine is stopped and the expected risk-state volume is mounted in the Compose configuration.
3. Recreate only the engine service from the already-built local image:

```bash
docker compose up -d --no-deps engine
```

Do not set `ENGINE_RISK_RESUME_AUTHORIZATION` or change risk limits to bypass the halt. Do not rebuild or restart the whole stack.

## Gate 4 — validation and stop conditions

Immediately inspect:

```bash
ENGINE_ID="$(docker compose ps -q engine)"
docker compose ps
docker inspect "$ENGINE_ID" --format 'Status={{.State.Status}} RestartCount={{.RestartCount}} ImageID={{.Image}} StartedAt={{.State.StartedAt}}'
docker logs --since 10m "$ENGINE_ID" 2>&1
```

Required evidence:

- Engine reaches healthy status and logs a successful startup.
- The halt log shows `diagnostics_origin=reconstructed_recovery_context` for the existing reconstructed case, with reason `max_drawdown`.
- The halt remains active; there is no resume authorization and no unexpected position or journal replay.
- The persisted snapshot is version 4 and retains the reconstructed marker/metrics.
- Gateway health/readiness and dashboard checks pass after the engine is healthy.
- Record the new container image ID, snapshot hash, journal hash, and health-check outputs.

Stop and preserve logs/state if startup fails, the snapshot is rejected, the halt is missing, diagnostics origin is unexpected, journal reconciliation differs unexpectedly, or downstream health checks fail. Do not delete temporary files or repeatedly restart to see whether it recovers.

## Rollback policy — do not blindly revert the binary

The pre-deployment engine understands version-3 snapshots, while the new engine writes version 4. The old binary must **not** be pointed at a version-4 snapshot. A direct image rollback without state-format planning can cause fail-closed startup.

If validation fails:

1. Stop only the newly deployed engine and confirm it has stopped.
2. Preserve a separate copy of the post-failure risk-state directory and logs before any restoration.
3. Compare post-failure state with the pre-deployment backup. Do not overwrite either copy.
4. If the active snapshot has been upgraded to version 4, do not start the old image against it. A version-3 backup may be restored only after the engine is stopped, after post-failure evidence is preserved, and after confirming no new journal records or legitimate state changes would be lost. If that cannot be established, stop and investigate rather than restoring.
5. If reverting to the old image is necessary, restore only the verified pre-deployment version-3 state under the conditions above, pin the known previous image ID explicitly, then start the engine and validate the existing halt. Do not rely on the mutable `:latest` tag for rollback.
6. Keep the halt active. Never authorize resume as a rollback shortcut.

Because the engine can write state while running, restoring a backup over a live volume is prohibited. Do not run `docker compose down -v`, remove volumes, or use destructive cleanup commands.

## Completion record

Record the maintenance start/end times, source commit, previous and deployed image IDs, backup path, snapshot/journal hashes before and after, engine logs, health checks, and whether rollback was required. Mark deployment complete only after the halt and downstream services are verified.
