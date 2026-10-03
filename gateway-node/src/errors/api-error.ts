import type { ApiErrorCode } from "../types/api.types.ts";

export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly statusCode: number;
  readonly retryAfterSeconds?: number;

  constructor(
    statusCode: number,
    code: ApiErrorCode,
    message: string,
    options: { readonly retryAfterSeconds?: number } = {},
  ) {
    super(message);

    this.name = "ApiError";
    this.code = code;
    this.statusCode = statusCode;
    this.retryAfterSeconds = options.retryAfterSeconds;
  }
}

export function invalidArgument(message: string): ApiError {
  return new ApiError(400, "INVALID_ARGUMENT", message);
}

export function unauthorized(message: string): ApiError {
  return new ApiError(401, "UNAUTHORIZED", message);
}

export function forbidden(message: string): ApiError {
  return new ApiError(403, "FORBIDDEN", message);
}

export function notFound(message: string): ApiError {
  return new ApiError(404, "NOT_FOUND", message);
}

export function conflict(message: string): ApiError {
  return new ApiError(409, "CONFLICT", message);
}

export function dependencyUnavailable(message: string): ApiError {
  return new ApiError(503, "DEPENDENCY_UNAVAILABLE", message);
}

export function rateLimited(retryAfterSeconds: number): ApiError {
  return new ApiError(429, "RATE_LIMITED", "Rate limit exceeded", {
    retryAfterSeconds,
  });
}

export function internalError(message = "Internal server error"): ApiError {
  return new ApiError(500, "INTERNAL_ERROR", message);
}
