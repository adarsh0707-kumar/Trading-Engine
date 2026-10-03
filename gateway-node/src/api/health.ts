import type { FastifyInstance } from "fastify";
import type { StatusProvider } from "../status/status.types.ts";
import type { HealthResponse, ReadinessResponse } from "../types/health.types.ts";

export interface HealthRouteOptions {
  readonly onReadinessChange?: (ready: boolean) => void;
}

export async function registerHealthRoutes(
  app: FastifyInstance,
  statusProvider: StatusProvider,
  options: HealthRouteOptions = {},
): Promise<void> {
  app.get<{ Reply: HealthResponse }>("/api/health", async () => ({
    status: "ok",
    service: "gateway",
  }));

  app.get<{ Reply: ReadinessResponse }>("/api/ready", async (_request, reply) => {
    const status = statusProvider.getStatus();
    const ready =
      status.engine === "connected" && status.analytics === "connected";

    options.onReadinessChange?.(ready);
    reply.code(ready ? 200 : 503);

    return {
      status: ready ? "ready" : "not_ready",
      service: "gateway",
      dependencies: status,
    };
  });
}
