export const FAILURE_CATEGORIES = [
  "connection",
  "timeout",
  "protocol",
  "validation",
  "queue_overflow",
  "dependency_unavailable",
  "processing",
  "shutdown",
] as const;

export type FailureCategory = (typeof FAILURE_CATEGORIES)[number];

const RECOVERABLE_CATEGORIES = new Set<FailureCategory>([
  "connection",
  "timeout",
  "queue_overflow",
  "dependency_unavailable",
]);

export class GatewayFailure extends Error {
  readonly category: FailureCategory;
  readonly recoverable: boolean;

  constructor(
    message: string,
    category: FailureCategory,
    recoverable = RECOVERABLE_CATEGORIES.has(category),
  ) {
    super(message);
    this.name = "GatewayFailure";
    this.category = category;
    this.recoverable = recoverable;
  }
}

export class ConnectionFailure extends GatewayFailure {
  constructor(message: string) {
    super(message, "connection");
  }
}

export class TimeoutFailure extends GatewayFailure {
  constructor(message: string) {
    super(message, "timeout");
  }
}

export class ProtocolFailure extends GatewayFailure {
  constructor(message: string) {
    super(message, "protocol", false);
  }
}

export class ValidationFailure extends GatewayFailure {
  constructor(message: string) {
    super(message, "validation", false);
  }
}

export class QueueOverflow extends GatewayFailure {
  constructor(message: string) {
    super(message, "queue_overflow");
  }
}

export class DependencyUnavailable extends GatewayFailure {
  constructor(message: string) {
    super(message, "dependency_unavailable");
  }
}

export class ProcessingFailure extends GatewayFailure {
  constructor(message: string) {
    super(message, "processing", false);
  }
}

export class ShutdownFailure extends GatewayFailure {
  constructor(message: string) {
    super(message, "shutdown", false);
  }
}

export function classifyFailure(
  value: unknown,
  fallback: FailureCategory = "processing",
): GatewayFailure {
  if (value instanceof GatewayFailure) {
    return value;
  }

  const message = value instanceof Error ? value.message : String(value);
  return new GatewayFailure(message, fallback);
}
