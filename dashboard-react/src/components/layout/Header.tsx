import ConnectionBadge from "../common/ConnectionBadge";

export default function Header() {
  return (
    <header className="header">
      <div className="header-context">
        <span className="header-eyebrow">TRADING TERMINAL</span>
        <strong>Market Command Center</strong>
      </div>

      <div className="header-actions">
        <span className="header-live-label">Gateway</span>
        <ConnectionBadge status="disconnected" />
      </div>
    </header>
  );
}
