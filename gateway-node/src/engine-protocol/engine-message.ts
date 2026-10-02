import {
  ENGINE_MESSAGE_TYPES,
  type EngineMessage,
  type EngineMessageType,
  type NormalizedEngineEvent,
} from "./engine-message.types.ts";

export class EngineMessageValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EngineMessageValidationError";
  }
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isEngineMessageType(
  value: unknown,
): value is EngineMessageType {
  return (
    typeof value === "string" &&
    (ENGINE_MESSAGE_TYPES as readonly string[]).includes(value)
  );
}

function requireString(
  value: unknown,
  field: string,
): string {
  if (typeof value !== "string") {
    throw new EngineMessageValidationError(
      `Engine message field '${field}' must be a string`,
    );
  }

  return value;
}

export function parseEngineMessage(
  value: unknown,
): EngineMessage {
  if (!isRecord(value)) {
    throw new EngineMessageValidationError(
      "Engine message must be a JSON object",
    );
  }

  const type = value["type"];

  if (!isEngineMessageType(type)) {
    throw new EngineMessageValidationError(
      "Engine message field 'type' is unsupported",
    );
  }

  return {
    type,
    requestId: requireString(
      value["request_id"],
      "request_id",
    ),
    timestamp: requireString(
      value["timestamp"],
      "timestamp",
    ),
    payload: requireString(
      value["payload"],
      "payload",
    ),
  };
}

export function normalizeEngineMessage(
  message: EngineMessage,
): NormalizedEngineEvent {
  const eventId = message.requestId.trim();

  if (eventId.length === 0) {
    throw new EngineMessageValidationError(
      "Engine message field 'request_id' must not be empty",
    );
  }

  if (message.timestamp.trim().length === 0) {
    throw new EngineMessageValidationError(
      "Engine message field 'timestamp' must not be empty",
    );
  }

  return {
    type: message.type,
    eventId,
    requestId: message.requestId,
    timestamp: message.timestamp,
    payload: message.payload,
  };
}


export function parseAndNormalizeEngineMessage(
  value: unknown,
): NormalizedEngineEvent {
  return normalizeEngineMessage(
    parseEngineMessage(value),
  );
}
