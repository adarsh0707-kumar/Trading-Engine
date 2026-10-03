export const MAX_ENGINE_REQUEST_ID_LENGTH = 256;
export const MAX_ENGINE_TIMESTAMP_LENGTH = 64;
export const MAX_TRANSPORT_PAYLOAD_BYTES = 1024 * 1024;

export function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function assertExactKeys(
  value: Record<string, unknown>,
  expectedKeys: readonly string[],
  label: string,
): void {
  const expected = new Set(expectedKeys);

  for (const key of Object.keys(value)) {
    if (!expected.has(key)) {
      throw new Error(`${label} contains unsupported field '${key}'`);
    }
  }

  for (const key of expectedKeys) {
    if (!(key in value)) {
      throw new Error(`${label} is missing required field '${key}'`);
    }
  }
}

export function validateBoundedString(
  value: unknown,
  field: string,
  maxLength: number,
): string {
  if (typeof value !== "string") {
    throw new Error(`${field} must be a string`);
  }

  if (value.length === 0) {
    throw new Error(`${field} must not be empty`);
  }

  if (value.length > maxLength) {
    throw new Error(`${field} exceeds the maximum length of ${maxLength}`);
  }

  return value;
}

export function validateIsoTimestamp(
  value: unknown,
  field: string,
): string {
  const timestamp = validateBoundedString(
    value,
    field,
    MAX_ENGINE_TIMESTAMP_LENGTH,
  );

  if (timestamp.trim() === "") {
    throw new Error(`${field} must not be empty`);
  }

  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$/.test(timestamp)) {
    throw new Error(`${field} must be an ISO-8601 UTC timestamp`);
  }

  if (!Number.isFinite(Date.parse(timestamp))) {
    throw new Error(`${field} must be a valid timestamp`);
  }

  return timestamp;
}

export function validateBoundedPositiveInteger(
  value: unknown,
  field: string,
  maxValue: number,
): number {
  if (!Number.isInteger(value) || (value as number) <= 0) {
    throw new Error(`${field} must be a positive integer`);
  }

  if ((value as number) > maxValue) {
    throw new Error(`${field} must be at most ${maxValue}`);
  }

  return value as number;
}

export function validateUniqueStringArray(
  value: unknown,
  field: string,
  maxItems: number,
): string[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`${field} must be a non-empty array`);
  }

  if (value.length > maxItems) {
    throw new Error(`${field} must contain at most ${maxItems} items`);
  }

  const values = value.map((item) => {
    if (typeof item !== "string" || item.length === 0) {
      throw new Error(`${field} must contain only non-empty strings`);
    }

    return item;
  });

  if (new Set(values).size !== values.length) {
    throw new Error(`${field} must not contain duplicate values`);
  }

  return values;
}
