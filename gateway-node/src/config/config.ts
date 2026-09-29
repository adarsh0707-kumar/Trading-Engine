export interface GatewayConfig {
  readonly host: string;
  readonly port: number;
}

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 8080;

function parsePort(value: string | undefined): number {
  if (value === undefined || value.trim() === "") {
    return DEFAULT_PORT;
  }

  const port = Number(value);

  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error(`Invalid GATEWAY_PORT: ${value}`);
  }

  return port;
}

export function loadConfig(
  environment: Record<string, string | undefined> = process.env,
): GatewayConfig {
  const host = environment.GATEWAY_HOST?.trim() || DEFAULT_HOST;

  if (host.length === 0) {
    throw new Error("GATEWAY_HOST must not be empty");
  }

  return Object.freeze({
    host,
    port: parsePort(environment.GATEWAY_PORT),
  });
}
