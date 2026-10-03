import type { FastifyInstance } from "fastify";

import type { EngineEventClient } from "../../engine/engine-event-client.ts";
import {
  apiErrorSchema,
  engineHealthResponseSchema,
} from "./schemas.ts";

export async function registerEngineHealthRoute(
  app: FastifyInstance,
  engineEventClient: EngineEventClient,
): Promise<void> {
  app.get("/api/v1/status/engine", {
    schema: {
      response: {
        200: engineHealthResponseSchema,
        404: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
  }, async () => ({
    data: engineEventClient.getHealth(),
  }));
}
