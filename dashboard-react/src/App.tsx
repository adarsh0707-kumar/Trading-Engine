import AppRouter from "./app/router";
import { LiveTradingProvider } from "./hooks/LiveTradingContext";

export default function App() {
  return (
    <LiveTradingProvider>
      <AppRouter />
    </LiveTradingProvider>
  );
}
