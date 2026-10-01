import type { FastifyInstance } from "fastify";

import { dependencyUnavailable, invalidArgument } from "../../errors/api-error.ts";
import type { EngineProvider } from "../../engine/engine.types.ts";
import {
  apiErrorSchema,
  engineActionResponseSchema,
} from "./schemas.ts";

export interface EngineRouteOptions {
  readonly engineProvider: EngineProvider;
}

function validateEmptyEngineBody(body: unknown): void {
  if (body === undefined) {
    return;
  }

  if (
    typeof body !== "object" ||
    body === null ||
    Array.isArray(body) ||
    Object.keys(body).length !== 0
  ) {
    throw invalidArgument("Request validation failed");
  }
}

export async function registerEngineRoutes(
  app: FastifyInstance,
  options: EngineRouteOptions,
): Promise<void> {
  app.post("/api/v1/engine/start", {
    schema: {
      response: {
        202: engineActionResponseSchema,
        400: apiErrorSchema,
        404: apiErrorSchema,
        503: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
    preValidation: async (request) => {
      validateEmptyEngineBody(request.body);
    },
  }, async (_request, reply) => {
    const result = options.engineProvider.start();

    if (result === null) {
      throw dependencyUnavailable("Engine control is unavailable");
    }

    return reply.status(202).send({
      data: result,
    });
  });

  app.post("/api/v1/engine/stop", {
    schema: {
      response: {
        202: engineActionResponseSchema,
        400: apiErrorSchema,
        404: apiErrorSchema,
        503: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
    preValidation: async (request) => {
      validateEmptyEngineBody(request.body);
    },
  }, async (_request, reply) => {
    const result = options.engineProvider.stop();

    if (result === null) {
      throw dependencyUnavailable("Engine control is unavailable");
    }

    return reply.status(202).send({
      data: result,
    });
  });

  app.post("/api/v1/engine/reset", {
    schema: {
      response: {
        202: engineActionResponseSchema,
        400: apiErrorSchema,
        404: apiErrorSchema,
        503: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
    preValidation: async (request) => {
      validateEmptyEngineBody(request.body);
    },
  }, async (_request, reply) => {
    const result = options.engineProvider.reset();

    if (result === null) {
      throw dependencyUnavailable("Engine control is unavailable");
    }

    return reply.status(202).send({
      data: result,
    });
  });
}
