import type { FastifyInstance } from "fastify";
import type { HealthResponse } from "../types/health.types.ts";

export async function registerHealthRoutes(
  app: FastifyInstance,
): Promise<void> {
  app.get<{ Reply: HealthResponse }>("/api/health", async () => ({
    status: "ok",
    service: "gateway",
  }));
}
