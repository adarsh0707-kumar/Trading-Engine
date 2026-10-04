import { NavLink } from "react-router-dom";
import { dashboardRoutes } from "../../app/router";

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">TE</div>
        <div>
          <strong>Trading Engine</strong>
          <span>Dashboard</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        {dashboardRoutes.map((route) => (
          <NavLink
            key={route.path}
            to={route.path}
            className={({ isActive }) =>
              `sidebar-link${isActive ? " sidebar-link-active" : ""}`
            }
          >
            {route.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
