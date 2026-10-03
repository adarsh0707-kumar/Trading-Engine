import {
  ENGINE_MESSAGE_TYPES,
  type EngineMessage,
  type EngineMessageType,
  type NormalizedEngineEvent,
} from "./engine-message.types.ts";
import {
  assertExactKeys,
  isRecord,
  validateBoundedString,
  validateIsoTimestamp,
  MAX_ENGINE_REQUEST_ID_LENGTH,
} from "../security/input-validation.ts";

export class EngineMessageValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EngineMessageValidationError";
  }
}

function isEngineMessageType(
  value: unknown,
): value is EngineMessageType {
  return (
    typeof value === "string" &&
    (ENGINE_MESSAGE_TYPES as readonly string[]).includes(value)
  );
}

function toValidationError(error: unknown): EngineMessageValidationError {
  return new EngineMessageValidationError(
    error instanceof Error
      ? error.message
      : "Engine message validation failed",
  );
}

export function parseEngineMessage(
  value: unknown,
): EngineMessage {
  if (!isRecord(value)) {
    throw new EngineMessageValidationError(
      "Engine message must be a JSON object",
    );
  }

  try {
    assertExactKeys(
      value,
      ["type", "request_id", "timestamp", "payload"],
      "Engine message",
    );

    const type = value["type"];

    if (!isEngineMessageType(type)) {
      throw new Error(
        "Engine message field 'type' is unsupported",
      );
    }

    return {
      type,
      requestId: validateBoundedString(
        value["request_id"],
        "Engine message field 'request_id'",
        MAX_ENGINE_REQUEST_ID_LENGTH,
      ),
      timestamp: validateIsoTimestamp(
        value["timestamp"],
        "Engine message field 'timestamp'",
      ),
      payload: validateBoundedString(
        value["payload"],
        "Engine message field 'payload'",
        1024 * 1024,
      ),
    };
  } catch (error) {
    throw toValidationError(error);
  }
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

  try {
    validateIsoTimestamp(
      message.timestamp,
      "Engine message field 'timestamp'",
    );
  } catch (error) {
    throw toValidationError(error);
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
