import Fastify, { type FastifyInstance } from "fastify";

import { registerHealthRoutes } from "./api/health.ts";
import { loadConfig, type GatewayConfig } from "./config/config.ts";

export interface GatewayServer {
  readonly app: FastifyInstance;
  readonly config: GatewayConfig;
  readonly start: () => Promise<void>;
  readonly stop: () => Promise<void>;
}

export function createGatewayServer(
  environment: Record<string, string | undefined> = process.env,
): GatewayServer {
  const config = loadConfig(environment);

  const app = Fastify({
    logger: {
      level: config.logging.level,
    },
    bodyLimit: config.http.bodyLimitBytes,
    connectionTimeout: config.http.requestTimeoutMs,
  });

  app.register(registerHealthRoutes);

  let started = false;

  const start = async (): Promise<void> => {
    if (started) {
      return;
    }

    await app.listen({
      host: config.gateway.host,
      port: config.gateway.port,
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
    config,
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

    gateway.app.log.info(
      {
        host: gateway.config.gateway.host,
        port: gateway.config.gateway.port,
      },
      "gateway_started",
    );
  } catch (error) {
    gateway.app.log.error({ error }, "gateway_start_failed");
    process.exit(1);
  }
}

if (import.meta.main) {
  await startGateway();
}
