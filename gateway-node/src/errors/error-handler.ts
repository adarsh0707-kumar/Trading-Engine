import type { FastifyError, FastifyInstance } from "fastify";

import { ApiError } from "./api-error.ts";
import type { ApiErrorBody } from "../types/api.types.ts";

function getRequestId(request: {
  readonly id: string;
}): string {
  return request.id;
}

function getPublicErrorMessage(
  code: ApiErrorBody["error"]["code"],
): string {
  switch (code) {
    case "INVALID_ARGUMENT":
      return "Request validation failed";
    case "UNAUTHORIZED":
      return "Authentication required";
    case "FORBIDDEN":
      return "Access denied";
    case "NOT_FOUND":
      return "Resource not found";
    case "CONFLICT":
      return "Request conflicts with the current state";
    case "DEPENDENCY_UNAVAILABLE":
      return "Required dependency is unavailable";
    case "RATE_LIMITED":
      return "Too many requests";
    case "INTERNAL_ERROR":
      return "Internal server error";
  }
}

function buildErrorBody(
  requestId: string,
  code: ApiErrorBody["error"]["code"],
  message: string,
): ApiErrorBody {
  return {
    error: {
      code,
      message,
      request_id: requestId,
    },
  };
}

export function registerErrorHandler(app: FastifyInstance): void {
  app.setNotFoundHandler((request, reply) => {
    return reply
      .status(404)
      .send(
        buildErrorBody(
          getRequestId(request),
          "NOT_FOUND",
          "Route not found",
        ),
      );
  });

  app.setErrorHandler((error: FastifyError, request, reply) => {
    const requestId = getRequestId(request);

    if (error.code === "FST_ERR_CTP_BODY_TOO_LARGE") {
      return reply
        .status(413)
        .send(
          buildErrorBody(
            requestId,
            "INVALID_ARGUMENT",
            "Request payload exceeds the configured maximum size",
          ),
        );
    }

    if (error instanceof ApiError) {
      return reply
        .status(error.statusCode)
        .send(
          buildErrorBody(
            requestId,
            error.code,
            getPublicErrorMessage(error.code),
          ),
        );
    }

    if (error.validation) {
      return reply
        .status(400)
        .send(
          buildErrorBody(
            requestId,
            "INVALID_ARGUMENT",
            "Request validation failed",
          ),
        );
    }

    request.log.error({ error }, "unhandled_request_error");

    return reply
      .status(500)
      .send(
        buildErrorBody(
          requestId,
          "INTERNAL_ERROR",
          getPublicErrorMessage("INTERNAL_ERROR"),
        ),
      );
  });
}
