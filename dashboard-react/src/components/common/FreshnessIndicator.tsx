import { useEffect, useState } from "react";
import { formatFreshnessAge, getFreshness, type FreshnessState } from "../../types/freshness";

interface FreshnessIndicatorProps {
  readonly updatedAt: string | number | null | undefined;
  readonly connected?: boolean;
  readonly staleAfterMs?: number;
  readonly label?: string;
}

function labelFor(state: FreshnessState): string {
  if (state === "fresh") return "LIVE";
  if (state === "stale") return "STALE";
  return "WAITING";
}

export default function FreshnessIndicator({
  updatedAt,
  connected = true,
  staleAfterMs = 15_000,
  label = "Data",
}: FreshnessIndicatorProps) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const timer = globalThis.setInterval(() => setTick((value) => value + 1), 5_000);
    return () => globalThis.clearInterval(timer);
  }, []);

  const freshness = getFreshness(updatedAt, { connected, staleAfterMs });

  return (
    <span
      className={"freshness-indicator freshness-indicator-" + freshness.state}
      title={freshness.updatedAt === null ? "No successful data snapshot yet" : label + " updated " + formatFreshnessAge(freshness.ageMs)}
      aria-label={label + ": " + labelFor(freshness.state) + ", " + formatFreshnessAge(freshness.ageMs)}
    >
      <span className="freshness-dot" aria-hidden="true" />
      {labelFor(freshness.state)} · {formatFreshnessAge(freshness.ageMs)}
    </span>
  );
}
