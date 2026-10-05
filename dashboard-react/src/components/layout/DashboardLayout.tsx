import { useState } from "react";
import { Outlet } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="app-main">
        <Header onMenuClick={() => setSidebarOpen(true)} />

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
