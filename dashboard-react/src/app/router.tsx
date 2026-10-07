import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import DashboardLayout from "../components/layout/DashboardLayout";
import Loading from "../components/common/Loading";

const Analytics = lazy(() => import("../pages/Analytics"));
const Dashboard = lazy(() => import("../pages/Dashboard"));
const Markets = lazy(() => import("../pages/Markets"));
const Risk = lazy(() => import("../pages/Risk"));
const System = lazy(() => import("../pages/System"));
const Trades = lazy(() => import("../pages/Trades"));

export const dashboardRoutes = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/markets", label: "Markets" },
  { path: "/trades", label: "Trades" },
  { path: "/analytics", label: "Analytics" },
  { path: "/risk", label: "Risk" },
  { path: "/system", label: "System" },
] as const;

export default function AppRouter() {
  return (
    <Suspense fallback={<div className="page-content"><Loading /></div>}>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/markets" element={<Markets />} />
          <Route path="/trades" element={<Trades />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/system" element={<System />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}
