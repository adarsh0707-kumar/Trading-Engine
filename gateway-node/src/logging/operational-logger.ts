import type { FastifyBaseLogger } from "fastify";

export type OperationalLogLevel = "info" | "warn" | "error";

export interface OperationalLogFields {
  readonly service?: string;
  readonly component?: string;
  readonly event?: string;
  readonly outcome?: string;
  readonly requestId?: string;
  readonly eventId?: string;
  readonly state?: string;
  readonly error?: unknown;
  readonly [key: string]: unknown;
}

export interface OperationalLogger {
  readonly info: (event: string, fields?: OperationalLogFields) => void;
  readonly warn: (event: string, fields?: OperationalLogFields) => void;
  readonly error: (event: string, fields?: OperationalLogFields) => void;
}

const SERVICE = "gateway";

function write(
  logger: FastifyBaseLogger,
  level: OperationalLogLevel,
  event: string,
  fields: OperationalLogFields = {},
): void {
  const { event: _ignoredEvent, service: _ignoredService, ...extra } = fields;

  logger[level](
    {
      service: SERVICE,
      event,
      ...extra,
    },
    event,
  );
}

export function createOperationalLogger(
  logger: FastifyBaseLogger,
  component: string,
): OperationalLogger {
  const withComponent = (
    level: OperationalLogLevel,
    event: string,
    fields?: OperationalLogFields,
  ): void => {
    write(logger, level, event, {
      component,
      ...fields,
    });
  };

  return {
    info: (event, fields) => withComponent("info", event, fields),
    warn: (event, fields) => withComponent("warn", event, fields),
    error: (event, fields) => withComponent("error", event, fields),
  };
}
