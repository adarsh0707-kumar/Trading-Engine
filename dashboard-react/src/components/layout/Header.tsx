import { useLocation } from "react-router-dom";
import ConnectionBadge from "../common/ConnectionBadge";
import { dashboardRoutes } from "../../app/router";

type HeaderProps = {
  onMenuClick: () => void;
};

export default function Header({ onMenuClick }: HeaderProps) {
  const location = useLocation();
  const currentRoute = dashboardRoutes.find(
    (route) => route.path === location.pathname,
  );
  const pageName = currentRoute?.label ?? "Dashboard";

  return (
    <header className="header">
      <button
        className="header-menu"
        type="button"
        aria-label="Open navigation"
        onClick={onMenuClick}
      >
        <span aria-hidden="true">☰</span>
      </button>

      <div className="header-context">
        <span className="header-eyebrow">TRADING TERMINAL / {pageName.toUpperCase()}</span>
        <strong>{pageName}</strong>
      </div>

      <div className="header-actions">
        <span className="header-live-label">Gateway</span>
        <ConnectionBadge status="disconnected" />
      </div>
    </header>
  );
}
