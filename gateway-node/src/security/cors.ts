import { isRecord, validateBoundedString } from "./input-validation.ts";

const MAX_CORS_ORIGINS = 32;
const MAX_CORS_ORIGIN_LENGTH = 2048;

export const DEFAULT_CORS_ORIGINS = ["http://localhost:5173"] as const;

function validateCorsOrigin(value: string): string {
  const origin = validateBoundedString(
    value,
    "CORS origin",
    MAX_CORS_ORIGIN_LENGTH,
  ).trim();

  if (
    origin === "*" ||
    origin === "null" ||
    origin.includes(",") ||
    /[\s\\]/.test(origin)
  ) {
    throw new Error(`Invalid CORS origin: ${origin}`);
  }

  let parsed: URL;

  try {
    parsed = new URL(origin);
  } catch {
    throw new Error(`Invalid CORS origin: ${origin}`);
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`Invalid CORS origin: ${origin}`);
  }

  if (
    parsed.username !== "" ||
    parsed.password !== "" ||
    parsed.pathname !== "/" ||
    parsed.search !== "" ||
    parsed.hash !== ""
  ) {
    throw new Error(`Invalid CORS origin: ${origin}`);
  }

  return parsed.origin;
}

export function parseCorsOrigins(
  environment: Record<string, string | undefined>,
): string[] {
  const configured = environment.CORS_ORIGINS?.trim();
  const legacy = environment.CORS_ORIGIN?.trim();
  const raw = configured !== undefined && configured !== ""
    ? configured
    : legacy !== undefined && legacy !== ""
      ? legacy
      : DEFAULT_CORS_ORIGINS.join(",");

  const values = raw.split(",").map((value) => value.trim());

  if (values.length === 0 || values.some((value) => value === "")) {
    throw new Error("CORS origins must contain only non-empty origins");
  }

  if (values.length > MAX_CORS_ORIGINS) {
    throw new Error(`CORS origins must contain at most ${MAX_CORS_ORIGINS} origins`);
  }

  const origins = values.map(validateCorsOrigin);

  if (new Set(origins).size !== origins.length) {
    throw new Error("CORS origins must not contain duplicates");
  }

  return origins;
}

export function isCorsOriginAllowed(
  allowedOrigins: readonly string[],
  origin: unknown,
): boolean {
  if (origin === undefined) {
    return true;
  }

  if (typeof origin !== "string") {
    return false;
  }

  return allowedOrigins.includes(origin);
}

export function createCorsOriginValidator(
  allowedOrigins: readonly string[],
): (origin: string | undefined, callback: (error: Error | null, allow?: boolean) => void) => void {
  if (!Array.isArray(allowedOrigins) || allowedOrigins.length === 0) {
    throw new Error("At least one CORS origin must be configured");
  }

  for (const origin of allowedOrigins) {
    validateCorsOrigin(origin);
  }

  return (origin, callback) => {
    callback(null, isCorsOriginAllowed(allowedOrigins, origin));
  };
}
