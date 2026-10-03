import type { FastifyError, FastifyInstance } from "fastify";

import { ApiError } from "./api-error.ts";
import type { ApiErrorBody } from "../types/api.types.ts";

function getRequestId(request: {
  readonly id: string;
}): string {
  return request.id;
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
        .send(buildErrorBody(requestId, error.code, error.message));
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
          "Internal server error",
        ),
      );
  });
}
