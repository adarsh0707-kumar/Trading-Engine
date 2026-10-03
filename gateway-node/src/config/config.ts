export interface GatewayConfig {
  readonly gateway: {
    readonly host: string;
    readonly port: number;
  };

  readonly engine: {
    readonly host: string;
    readonly port: number;
    readonly connectTimeoutMs: number;
    readonly heartbeatTimeoutMs: number;
    readonly requestTimeoutMs: number;
    readonly reconnectInitialDelayMs: number;
    readonly reconnectMaxDelayMs: number;
    readonly reconnectMaxAttempts: number;
  };

  readonly analytics: {
    readonly host: string;
    readonly port: number;
    readonly requestTimeoutMs: number;
    readonly connectTimeoutMs: number;
    readonly reconnectInitialDelayMs: number;
    readonly reconnectMaxDelayMs: number;
    readonly reconnectMaxAttempts: number;
    readonly maxQueueSize: number;
  };

  readonly websocket: {
    readonly path: string;
    readonly heartbeatIntervalMs: number;
    readonly maxPayloadBytes: number;
    readonly maxQueueSize: number;
  };

  readonly http: {
    readonly requestTimeoutMs: number;
    readonly bodyLimitBytes: number;
  };

  readonly logging: {
    readonly level: string;
  };

  readonly metrics: {
    readonly enabled: boolean;
    readonly path: string;
  };

  readonly cors: {
    readonly origin: string;
  };
}

const DEFAULTS = {
  gateway: {
    host: "127.0.0.1",
    port: 8080,
  },

  engine: {
    host: "127.0.0.1",
    port: 9000,
    connectTimeoutMs: 5000,
    heartbeatTimeoutMs: 15000,
    requestTimeoutMs: 5000,
    reconnectInitialDelayMs: 500,
    reconnectMaxDelayMs: 10000,
    reconnectMaxAttempts: 10,
  },

  analytics: {
    host: "127.0.0.1",
    port: 8000,
    requestTimeoutMs: 5000,
    connectTimeoutMs: 5000,
    reconnectInitialDelayMs: 500,
    reconnectMaxDelayMs: 10000,
    reconnectMaxAttempts: 10,
    maxQueueSize: 256,
  },

  websocket: {
    path: "/ws",
    heartbeatIntervalMs: 30000,
    maxPayloadBytes: 1024 * 1024,
    maxQueueSize: 256,
  },

  http: {
    requestTimeoutMs: 10000,
    bodyLimitBytes: 1024 * 1024,
  },

  logging: {
    level: "info",
  },

  metrics: {
    enabled: true,
    path: "/metrics",
  },

  cors: {
    origin: "http://localhost:5173",
  },
} as const;

function getString(
  environment: Record<string, string | undefined>,
  name: string,
  fallback: string,
): string {
  const value = environment[name]?.trim();

  if (value === undefined || value === "") {
    return fallback;
  }

  return value;
}

function parseHost(
  environment: Record<string, string | undefined>,
  name: string,
  fallback: string,
): string {
  const value = environment[name]?.trim();

  if (value === undefined || value === "") {
    return fallback;
  }

  if (/\s/.test(value)) {
    throw new Error(`Invalid ${name}: ${value}`);
  }

  if (
    !/^[a-zA-Z0-9.-]+$/.test(value) ||
    value.startsWith(".") ||
    value.endsWith(".") ||
    value.startsWith("-") ||
    value.endsWith("-") ||
    value.includes("..")
  ) {
    throw new Error(`Invalid ${name}: ${value}`);
  }

  return value;
}

function parsePort(
  environment: Record<string, string | undefined>,
  name: string,
  fallback: number,
): number {
  const value = environment[name]?.trim();

  if (value === undefined || value === "") {
    return fallback;
  }

  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 65535) {
    throw new Error(`Invalid ${name}: ${value}`);
  }

  return parsed;
}

function parsePositiveInteger(
  environment: Record<string, string | undefined>,
  name: string,
  fallback: number,
): number {
  const value = environment[name]?.trim();

  if (value === undefined || value === "") {
    return fallback;
  }

  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`Invalid ${name}: ${value}`);
  }

  return parsed;
}

function parseNonNegativeInteger(
  environment: Record<string, string | undefined>,
  name: string,
  fallback: number,
): number {
  const value = environment[name]?.trim();

  if (value === undefined || value === "") {
    return fallback;
  }

  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`Invalid ${name}: ${value}`);
  }

  return parsed;
}

function parseBoolean(
  environment: Record<string, string | undefined>,
  name: string,
  fallback: boolean,
): boolean {
  const value = environment[name]?.trim().toLowerCase();

  if (value === undefined || value === "") {
    return fallback;
  }

  if (value === "true") {
    return true;
  }

  if (value === "false") {
    return false;
  }

  throw new Error(`Invalid ${name}: ${environment[name]}`);
}

function parsePath(
  environment: Record<string, string | undefined>,
  name: string,
  fallback: string,
): string {
  const value = getString(environment, name, fallback);

  if (!value.startsWith("/")) {
    throw new Error(`Invalid ${name}: ${value}`);
  }

  return value;
}

export function loadConfig(
  environment: Record<string, string | undefined> = process.env,
): GatewayConfig {
  const config = Object.freeze({
    gateway: Object.freeze({
      host: parseHost(
        environment,
        "GATEWAY_HOST",
        DEFAULTS.gateway.host,
      ),
      port: parsePort(
        environment,
        "GATEWAY_PORT",
        DEFAULTS.gateway.port,
      ),
    }),

    engine: Object.freeze({
      host: parseHost(
        environment,
        "ENGINE_HOST",
        DEFAULTS.engine.host,
      ),
      port: parsePort(
        environment,
        "ENGINE_PORT",
        DEFAULTS.engine.port,
      ),
      connectTimeoutMs: parsePositiveInteger(
        environment,
        "ENGINE_CONNECT_TIMEOUT_MS",
        DEFAULTS.engine.connectTimeoutMs,
      ),
      heartbeatTimeoutMs: parsePositiveInteger(
        environment,
        "ENGINE_HEARTBEAT_TIMEOUT_MS",
        DEFAULTS.engine.heartbeatTimeoutMs,
      ),
      requestTimeoutMs: parsePositiveInteger(
        environment,
        "ENGINE_REQUEST_TIMEOUT_MS",
        DEFAULTS.engine.requestTimeoutMs,
      ),
      reconnectInitialDelayMs: parseNonNegativeInteger(
        environment,
        "ENGINE_RECONNECT_INITIAL_DELAY_MS",
        DEFAULTS.engine.reconnectInitialDelayMs,
      ),
      reconnectMaxDelayMs: parseNonNegativeInteger(
        environment,
        "ENGINE_RECONNECT_MAX_DELAY_MS",
        DEFAULTS.engine.reconnectMaxDelayMs,
      ),
      reconnectMaxAttempts: parseNonNegativeInteger(
        environment,
        "ENGINE_RECONNECT_MAX_ATTEMPTS",
        DEFAULTS.engine.reconnectMaxAttempts,
      ),
    }),

    analytics: Object.freeze({
      host: parseHost(
        environment,
        "ANALYTICS_HOST",
        DEFAULTS.analytics.host,
      ),
      port: parsePort(
        environment,
        "ANALYTICS_PORT",
        DEFAULTS.analytics.port,
      ),
      requestTimeoutMs: parsePositiveInteger(
        environment,
        "ANALYTICS_REQUEST_TIMEOUT_MS",
        DEFAULTS.analytics.requestTimeoutMs,
      ),
      connectTimeoutMs: parsePositiveInteger(
        environment,
        "ANALYTICS_CONNECT_TIMEOUT_MS",
        DEFAULTS.analytics.connectTimeoutMs,
      ),
      reconnectInitialDelayMs: parseNonNegativeInteger(
        environment,
        "ANALYTICS_RECONNECT_INITIAL_DELAY_MS",
        DEFAULTS.analytics.reconnectInitialDelayMs,
      ),
      reconnectMaxDelayMs: parseNonNegativeInteger(
        environment,
        "ANALYTICS_RECONNECT_MAX_DELAY_MS",
        DEFAULTS.analytics.reconnectMaxDelayMs,
      ),
      reconnectMaxAttempts: parseNonNegativeInteger(
        environment,
        "ANALYTICS_RECONNECT_MAX_ATTEMPTS",
        DEFAULTS.analytics.reconnectMaxAttempts,
      ),
      maxQueueSize: parseNonNegativeInteger(
        environment,
        "ANALYTICS_MAX_QUEUE_SIZE",
        DEFAULTS.analytics.maxQueueSize,
      ),
    }),

    websocket: Object.freeze({
      path: parsePath(
        environment,
        "WEBSOCKET_PATH",
        DEFAULTS.websocket.path,
      ),
      heartbeatIntervalMs: parsePositiveInteger(
        environment,
        "WEBSOCKET_HEARTBEAT_INTERVAL_MS",
        DEFAULTS.websocket.heartbeatIntervalMs,
      ),
      maxPayloadBytes: parsePositiveInteger(
        environment,
        "WEBSOCKET_MAX_PAYLOAD_BYTES",
        DEFAULTS.websocket.maxPayloadBytes,
      ),
      maxQueueSize: parsePositiveInteger(
        environment,
        "WEBSOCKET_MAX_QUEUE_SIZE",
        DEFAULTS.websocket.maxQueueSize,
      ),
    }),

    http: Object.freeze({
      requestTimeoutMs: parsePositiveInteger(
        environment,
        "HTTP_REQUEST_TIMEOUT_MS",
        DEFAULTS.http.requestTimeoutMs,
      ),
      bodyLimitBytes: parsePositiveInteger(
        environment,
        "HTTP_BODY_LIMIT_BYTES",
        DEFAULTS.http.bodyLimitBytes,
      ),
    }),

    logging: Object.freeze({
      level: getString(
        environment,
        "LOG_LEVEL",
        DEFAULTS.logging.level,
      ),
    }),

    metrics: Object.freeze({
      enabled: parseBoolean(
        environment,
        "METRICS_ENABLED",
        DEFAULTS.metrics.enabled,
      ),
      path: parsePath(
        environment,
        "METRICS_PATH",
        DEFAULTS.metrics.path,
      ),
    }),

    cors: Object.freeze({
      origin: getString(
        environment,
        "CORS_ORIGIN",
        DEFAULTS.cors.origin,
      ),
    }),
  });

  if (
    config.engine.reconnectInitialDelayMs >
    config.engine.reconnectMaxDelayMs
  ) {
    throw new Error(
      "Invalid engine reconnect configuration: ENGINE_RECONNECT_INITIAL_DELAY_MS must be less than or equal to ENGINE_RECONNECT_MAX_DELAY_MS",
    );
  }

  if (
    config.analytics.reconnectInitialDelayMs >
    config.analytics.reconnectMaxDelayMs
  ) {
    throw new Error(
      "Invalid analytics reconnect configuration: ANALYTICS_RECONNECT_INITIAL_DELAY_MS must be less than or equal to ANALYTICS_RECONNECT_MAX_DELAY_MS",
    );
  }

  return config;
}
