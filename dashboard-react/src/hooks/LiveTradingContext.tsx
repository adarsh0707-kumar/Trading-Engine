import { createContext, useContext, type ReactNode } from "react";
import { useLiveTradingData, type LiveTradingData } from "../hooks/useLiveTradingData";

const LiveTradingContext = createContext<LiveTradingData | null>(null);

export function LiveTradingProvider({ children }: { readonly children: ReactNode }) {
  const data = useLiveTradingData();
  return <LiveTradingContext.Provider value={data}>{children}</LiveTradingContext.Provider>;
}

export function useLiveTrading(): LiveTradingData {
  const value = useContext(LiveTradingContext);
  if (value === null) {
    throw new Error("useLiveTrading must be used within LiveTradingProvider");
  }
  return value;
}
