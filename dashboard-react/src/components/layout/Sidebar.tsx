import { NavLink } from "react-router-dom";
import { dashboardRoutes } from "../../app/router";

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">TE</div>
        <div>
          <strong>Trading Engine</strong>
          <span>Command Center</span>
        </div>
      </div>

      <div className="sidebar-section-label">Workspace</div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        {dashboardRoutes.map((route, index) => (
          <NavLink
            key={route.path}
            to={route.path}
            className={({ isActive }) =>
              `sidebar-link${isActive ? " sidebar-link-active" : ""}`
            }
          >
            <span className="sidebar-link-index">
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
