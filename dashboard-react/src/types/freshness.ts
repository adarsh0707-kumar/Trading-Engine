export type FreshnessState = "fresh" | "stale" | "unknown";

export interface FreshnessInfo {
  readonly state: FreshnessState;
  readonly updatedAt: number | null;
  readonly ageMs: number | null;
}

export function getFreshness(
  updatedAt: string | number | null | undefined,
  options: { readonly staleAfterMs?: number; readonly connected?: boolean; readonly now?: number } = {},
): FreshnessInfo {
  if (updatedAt === null || updatedAt === undefined) return { state: "unknown", updatedAt: null, ageMs: null };
  const timestamp = typeof updatedAt === "number" ? updatedAt : new Date(updatedAt).getTime();
  if (!Number.isFinite(timestamp)) return { state: "unknown", updatedAt: null, ageMs: null };
  const ageMs = Math.max(0, (options.now ?? Date.now()) - timestamp);
  return {
    state: (options.connected ?? true) && ageMs <= (options.staleAfterMs ?? 15_000) ? "fresh" : "stale",
    updatedAt: timestamp,
    ageMs,
  };
}

export function formatFreshnessAge(ageMs: number | null): string {
  if (ageMs === null) return "No data";
  const seconds = Math.floor(ageMs / 1000);
  if (seconds < 60) return seconds + "s ago";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes + "m ago";
  return Math.floor(minutes / 60) + "h ago";
}
