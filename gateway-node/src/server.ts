import Fastify, { type FastifyInstance } from "fastify";

import { loadConfig } from "./config/config.ts";
import { registerHealthRoutes } from "./api/health.ts";

export interface GatewayServer {
  readonly app: FastifyInstance;
  readonly start: () => Promise<void>;
  readonly stop: () => Promise<void>;
}

export function createGatewayServer(): GatewayServer {
  const config = loadConfig();

  const app = Fastify({
    logger: true,
  });

  app.register(registerHealthRoutes);

  let started = false;

  const start = async (): Promise<void> => {
    if (started) {
      return;
    }

    await app.listen({
      host: config.host,
      port: config.port,
    });

    started = true;
  };

  const stop = async (): Promise<void> => {
    if (!started) {
      return;
    }

    await app.close();
    started = false;
  };

  return {
    app,
    start,
    stop,
  };
}

export async function startGateway(): Promise<void> {
  const gateway = createGatewayServer();

  const shutdown = async (signal: string): Promise<void> => {
    gateway.app.log.info({ signal }, "gateway_shutdown_started");

    try {
      await gateway.stop();
      gateway.app.log.info("gateway_shutdown_completed");
      process.exit(0);
    } catch (error) {
      gateway.app.log.error({ error }, "gateway_shutdown_failed");
      process.exit(1);
    }
  };

  process.once("SIGINT", () => {
    void shutdown("SIGINT");
  });

  process.once("SIGTERM", () => {
    void shutdown("SIGTERM");
  });

  try {
    await gateway.start();
    gateway.app.log.info("gateway_started");
  } catch (error) {
    gateway.app.log.error({ error }, "gateway_start_failed");
    process.exit(1);
  }
}

if (import.meta.main) {
  await startGateway();
}
