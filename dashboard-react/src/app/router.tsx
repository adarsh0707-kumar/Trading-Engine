import { Navigate, Route, Routes } from "react-router-dom";
import DashboardLayout from "../components/layout/DashboardLayout";
import Analytics from "../pages/Analytics";
import Dashboard from "../pages/Dashboard";
import Markets from "../pages/Markets";
import Risk from "../pages/Risk";
import System from "../pages/System";
import Trades from "../pages/Trades";

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
  );
}
