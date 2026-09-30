import client from "prom-client";

const registry = new client.Registry();

client.collectDefaultMetrics({
  register: registry,
});

export interface GatewayMetrics {
  readonly registry: client.Registry;
  readonly contentType: string;
  readonly getMetrics: () => Promise<string>;
}

export function createGatewayMetrics(): GatewayMetrics {
  return {
    registry,
    contentType: registry.contentType,
    getMetrics: () => registry.metrics(),
  };
}
