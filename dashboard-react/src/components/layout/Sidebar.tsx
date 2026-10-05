import { NavLink } from "react-router-dom";
import { dashboardRoutes } from "../../app/router";

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

export default function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <aside className={`sidebar${open ? " sidebar-open" : ""}`}>
      <div className="sidebar-brand">
        <div className="sidebar-logo" aria-hidden="true">TE</div>
        <div>
          <strong>Trading Engine</strong>
          <span>Command Center</span>
        </div>
        <button
          className="sidebar-close"
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
        >
          ×
        </button>
      </div>

      <div className="sidebar-section-label">Workspace</div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        {dashboardRoutes.map((route, index) => (
          <NavLink
            key={route.path}
            to={route.path}
            onClick={onClose}
            className={({ isActive }) =>
              `sidebar-link${isActive ? " sidebar-link-active" : ""}`
            }
          >
            <span className="sidebar-link-index" aria-hidden="true">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span>{route.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-footer-dot" aria-hidden="true" />
        <span>Gateway boundary</span>
      </div>
    </aside>
  );
}
