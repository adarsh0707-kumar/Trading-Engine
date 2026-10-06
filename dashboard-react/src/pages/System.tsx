import { useMemo } from "react";
import { useSystemStatus } from "../hooks/useSystemStatus";

function formatTime(value: number | null): string {
  if (value === null) return "—";
  return new Date(value).toLocaleString();
}

function formatAge(value: number | null, now: number): string {
  if (value === null) return "—";
  const seconds = Math.max(0, Math.floor((now - value) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ago`;
}

function statusLabel(value: string | undefined): string {
  return value?.replace(/_/g, " ").toUpperCase() ?? "UNKNOWN";
}

function statusClass(value: string | undefined): string {
  if (value === "connected" || value === "ok") return "system-status system-status-ok";
  if (value === "connecting") return "system-status system-status-warning";
  return "system-status system-status-error";
}

export default function System() {
  const { gateway, engine, state, error, refreshedAt, refresh } = useSystemStatus();
  const now = Date.now();

  const overallReady = gateway?.engine === "connected" && gateway.analytics === "connected";
  const overallClass = overallReady
    ? "system-status system-status-ok"
    : gateway === null
      ? "system-status system-status-warning"
      : "system-status system-status-error";

  const heartbeatAge = useMemo(
    () => formatAge(engine?.lastHeartbeatAt ?? null, now),
    [engine?.lastHeartbeatAt, now],
  );

  return (
    <div className="system-page">
      <header className="page-header dashboard-hero">
        <div>
          <span className="page-kicker">SYSTEM / 06</span>
          <h1>System Status</h1>
          <p>Live Gateway, Engine and Analytics connectivity from the existing status contracts.</p>
        </div>
        <span className={overallClass}>
          {overallReady ? "READY" : gateway === null ? "CHECKING" : "DEGRADED"}
        </span>
      </header>

      {state === "error" && gateway === null ? (
        <div className="state-message state-error system-error">
          <span>{error ?? "Unable to load system status."}</span>
          <button type="button" onClick={() => void refresh()}>Retry</button>
        </div>
      ) : (
        <>
          {error !== null && (
            <div className="state-message state-error system-inline-error" role="alert">
              <span>{error}</span>
              <button type="button" onClick={() => void refresh()}>Retry</button>
            </div>
          )}

          <section className="system-service-grid" aria-label="Service status">
            <article className="system-service-card system-service-card-dark">
              <span>GATEWAY</span>
              <strong>{statusLabel(gateway?.gateway)}</strong>
              <small>External REST and WebSocket boundary</small>
            </article>

            <article className="system-service-card">
              <span>ENGINE</span>
              <strong>{statusLabel(gateway?.engine)}</strong>
              <small>C++ TCP event connection</small>
            </article>

            <article className="system-service-card">
              <span>ANALYTICS</span>
              <strong>{statusLabel(gateway?.analytics)}</strong>
              <small>Python analytics connection</small>
            </article>
          </section>

          <section className="system-layout">
            <article className="system-panel">
              <div className="section-heading">
                <div>
                  <span className="panel-eyebrow">ENGINE HEALTH</span>
                  <h2>Connection telemetry</h2>
                </div>
                <span className={statusClass(engine?.state)}>
                  {statusLabel(engine?.state)}
                </span>
              </div>

              <div className="system-stat-grid">
                <div><span>Connected at</span><strong>{formatTime(engine?.connectedAt ?? null)}</strong></div>
                <div><span>Last message</span><strong>{formatAge(engine?.lastMessageAt ?? null, now)}</strong></div>
                <div><span>Last heartbeat</span><strong>{heartbeatAge}</strong></div>
                <div><span>Reconnect attempts</span><strong>{engine?.reconnectAttempts ?? "—"}</strong></div>
              </div>

              <div className="system-note">
                <span className="panel-eyebrow">SOURCE OF TRUTH</span>
                <p>
                  Engine connectivity and heartbeat telemetry come directly from the Gateway's
                  engine event client. The dashboard does not infer transport state from market data.
                </p>
              </div>
            </article>

            <article className="system-panel">
              <div className="section-heading">
                <div>
                  <span className="panel-eyebrow">RUNTIME</span>
                  <h2>Service readiness</h2>
                </div>
              </div>

              <div className="system-dependency-list">
                <div>
                  <span>Gateway</span>
                  <strong className={statusClass(gateway?.gateway)}> {statusLabel(gateway?.gateway)} </strong>
                </div>
                <div>
                  <span>Engine dependency</span>
                  <strong className={statusClass(gateway?.engine)}> {statusLabel(gateway?.engine)} </strong>
                </div>
                <div>
                  <span>Analytics dependency</span>
                  <strong className={statusClass(gateway?.analytics)}> {statusLabel(gateway?.analytics)} </strong>
                </div>
              </div>

              <div className="system-footer">
                <span>
                  {refreshedAt === null ? "Waiting for first status snapshot" : `Updated ${formatTime(refreshedAt)}`}
                </span>
                <button type="button" onClick={() => void refresh()}>Refresh status</button>
              </div>
            </article>
          </section>
        </>
      )}
    </div>
  );
}
