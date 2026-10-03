import { rateLimited } from "../errors/api-error.ts";

export interface RateLimitOptions {
  readonly enabled?: boolean;
  readonly maxRequests: number;
  readonly windowMs: number;
  readonly maxClients?: number;
  readonly now?: () => number;
}

interface Bucket {
  count: number;
  resetAt: number;
}

export interface RateLimitDecision {
  readonly allowed: boolean;
  readonly retryAfterSeconds: number;
}

export interface RateLimiter {
  readonly enabled: boolean;
  readonly check: (key: string) => RateLimitDecision;
  readonly reset: () => void;
  readonly size: () => number;
}

const DEFAULT_MAX_CLIENTS = 10_000;

export function createRateLimiter(options: RateLimitOptions): RateLimiter {
  if (!Number.isInteger(options.maxRequests) || options.maxRequests <= 0) {
    throw new Error("maxRequests must be a positive integer");
  }

  if (!Number.isInteger(options.windowMs) || options.windowMs <= 0) {
    throw new Error("windowMs must be a positive integer");
  }

  const maxClients = options.maxClients ?? DEFAULT_MAX_CLIENTS;
  if (!Number.isInteger(maxClients) || maxClients <= 0) {
    throw new Error("maxClients must be a positive integer");
  }

  const enabled = options.enabled ?? true;
  const now = options.now ?? Date.now;
  const buckets = new Map<string, Bucket>();

  const evictExpired = (timestamp: number): void => {
    for (const [key, bucket] of buckets) {
      if (bucket.resetAt <= timestamp) {
        buckets.delete(key);
      }
    }
  };

  const check = (key: string): RateLimitDecision => {
    const timestamp = now();
    evictExpired(timestamp);

    let bucket = buckets.get(key);

    if (!bucket) {
      if (buckets.size >= maxClients) {
        const oldestKey = buckets.keys().next().value;
        if (oldestKey !== undefined) {
          buckets.delete(oldestKey);
        }
      }

      bucket = {
        count: 0,
        resetAt: timestamp + options.windowMs,
      };
      buckets.set(key, bucket);
    }

    if (bucket.count >= options.maxRequests) {
      return {
        allowed: false,
        retryAfterSeconds: Math.max(
          1,
          Math.ceil((bucket.resetAt - timestamp) / 1000),
        ),
      };
    }

    bucket.count += 1;

    return {
      allowed: true,
      retryAfterSeconds: 0,
    };
  };

  return {
    enabled,
    check,
    reset: () => buckets.clear(),
    size: () => buckets.size,
  };
}

export function assertRateLimit(
  limiter: RateLimiter,
  key: string,
): void {
  if (!limiter.enabled) {
    return;
  }

  const decision = limiter.check(key);

  if (!decision.allowed) {
    throw rateLimited(decision.retryAfterSeconds);
  }
}
