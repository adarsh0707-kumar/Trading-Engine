import type { FastifyInstance } from "fastify";

import type { StatusProvider } from "../../status/status.types.ts";
import {
  apiErrorSchema,
  statusResponseSchema,
} from "./schemas.ts";

export async function registerStatusRoute(
  app: FastifyInstance,
  statusProvider: StatusProvider,
): Promise<void> {
  app.get("/api/v1/status", {
    schema: {
      response: {
        200: statusResponseSchema,
        404: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
  }, async () => ({
    data: statusProvider.getStatus(),
  }));
}
