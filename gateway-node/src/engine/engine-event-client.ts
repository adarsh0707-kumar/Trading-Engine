import { Socket, type Socket as NetSocket } from "node:net";

import { ConnectionFailure, ProtocolFailure, TimeoutFailure } from "../resilience/error-model.ts";

import {
  createEngineProtocol,
  type EngineProtocol,
} from "../engine-protocol/engine-protocol.ts";
import {
  normalizeEngineEvent,
  type NormalizedEngineEventResult,
} from "../engine-protocol/engine-event.ts";

export interface EngineEventClientOptions {
  readonly host: string;
  readonly port: number;
  readonly connectTimeoutMs: number;
  readonly reconnectInitialDelayMs: number;
  readonly reconnectMaxDelayMs: number;
  readonly reconnectMaxAttempts: number;
  readonly onEvent: (event: NormalizedEngineEventResult) => void;
  readonly onError?: (error: Error) => void;
  readonly onStateChange?: (
    state: "connecting" | "connected" | "disconnected",
  ) => void;
  readonly socketFactory?: () => NetSocket;
  readonly protocolFactory?: () => EngineProtocol;
}

export interface EngineEventClient {
  readonly start: () => void;
  readonly stop: () => void;
  readonly isConnected: () => boolean;
}

function toError(value: unknown): Error {
  return value instanceof Error ? value : new Error(String(value));
}

function frame(payload: string): Buffer {
  const body = Buffer.from(payload, "utf8");
  const result = Buffer.allocUnsafe(4 + body.length);

  result.writeUInt32BE(body.length, 0);
  body.copy(result, 4);

  return result;
}

function heartbeatResponse(requestId: string, timestamp: string): Buffer {
  return frame(
    JSON.stringify({
      type: "HEARTBEAT",
      request_id: requestId,
      timestamp,
      payload: "OK",
    }),
  );
}

export function createEngineEventClient(
  options: EngineEventClientOptions,
): EngineEventClient {
  let socket: NetSocket | undefined;
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let connectTimer: ReturnType<typeof setTimeout> | undefined;
  let running = false;
  let connected = false;
  let reconnectAttempts = 0;

  const clearTimers = (): void => {
    if (reconnectTimer !== undefined) {
      clearTimeout(reconnectTimer);
      reconnectTimer = undefined;
    }

    if (connectTimer !== undefined) {
      clearTimeout(connectTimer);
      connectTimer = undefined;
    }
  };

  const emitError = (error: unknown): void => {
    options.onError?.(toError(error));
  };

  const emitConnectionError = (error: unknown): void => {
    const normalized = toError(error);
    emitError(normalized instanceof ConnectionFailure ? normalized : new ConnectionFailure(normalized.message));
  };

  const disconnect = (): void => {
    if (connected) {
      connected = false;
      options.onStateChange?.("disconnected");
    }

    if (socket !== undefined) {
      socket.removeAllListeners();
      socket.destroy();
      socket = undefined;
    }

  };

  const scheduleReconnect = (): void => {
    if (!running || reconnectTimer !== undefined) {
      return;
    }

    if (
      options.reconnectMaxAttempts > 0 &&
      reconnectAttempts >= options.reconnectMaxAttempts
    ) {
      return;
    }

    const delay = Math.min(
      options.reconnectInitialDelayMs *
        2 ** reconnectAttempts,
      options.reconnectMaxDelayMs,
    );

    reconnectAttempts += 1;

    reconnectTimer = setTimeout(() => {
      reconnectTimer = undefined;
      connect();
    }, delay);
  };

  const handleClose = (closedSocket: NetSocket, closedProtocol: EngineProtocol): void => {
    const hadSocket = socket === closedSocket;

    if (connectTimer !== undefined) {
      clearTimeout(connectTimer);
      connectTimer = undefined;
    }

    if (socket !== closedSocket) return;

    socket = undefined;

    if (connected) {
      connected = false;
      options.onStateChange?.("disconnected");
    } else if (hadSocket) {
      options.onStateChange?.("disconnected");
    }

    closedProtocol.reset();

    if (running) {
      scheduleReconnect();
    }
  };

  const handleData = (nextSocket: NetSocket, nextProtocol: EngineProtocol, chunk: Buffer): void => {
    try {
      const messages = nextProtocol.push(
        new Uint8Array(
          chunk.buffer,
          chunk.byteOffset,
          chunk.byteLength,
        ),
      );

      for (const message of messages) {
        if (message.type === "HEARTBEAT") {
          if (socket !== nextSocket) return;
          nextSocket.write(
            heartbeatResponse(
              message.requestId,
              message.timestamp,
            ),
          );
          continue;
        }

        if (message.type !== "TRADE") {
          continue;
        }

        options.onEvent(normalizeEngineEvent(message));
      }
    } catch (error) {
      const normalized = toError(error);
      emitError(normalized instanceof ProtocolFailure ? normalized : new ProtocolFailure(normalized.message));
      if (socket === nextSocket) nextSocket.destroy();
    }
  };

  function connect(): void {
    if (!running || socket !== undefined) {
      return;
    }

    options.onStateChange?.("connecting");

    const nextSocket =
      options.socketFactory?.() ?? new Socket();

    socket = nextSocket;
    const nextProtocol =
      options.protocolFactory?.() ?? createEngineProtocol();

    const cleanupConnectTimer = (): void => {
      if (connectTimer !== undefined) {
        clearTimeout(connectTimer);
        connectTimer = undefined;
      }
    };

    nextSocket.setNoDelay(true);

    nextSocket.once("connect", () => {
      cleanupConnectTimer();

      if (!running || socket !== nextSocket) {
        nextSocket.destroy();
        return;
      }

      connected = true;
      reconnectAttempts = 0;
      options.onStateChange?.("connected");
    });

    nextSocket.on("data", (chunk) => handleData(nextSocket, nextProtocol, Buffer.from(chunk)));

    nextSocket.once("error", (error) => {
      if (socket === nextSocket) emitConnectionError(error);
    });

    nextSocket.once("close", () => handleClose(nextSocket, nextProtocol));

    connectTimer = setTimeout(() => {
      connectTimer = undefined;

      if (socket !== nextSocket || connected || !running) {
        return;
      }

      emitError(
        new TimeoutFailure(
          `Engine connection timed out after ${options.connectTimeoutMs}ms`,
        ),
      );

      nextSocket.destroy();
    }, options.connectTimeoutMs);

    nextSocket.connect(options.port, options.host);
  }

  const start = (): void => {
    if (running) {
      return;
    }

    running = true;
    reconnectAttempts = 0;
    clearTimers();
    connect();
  };

  const stop = (): void => {
    if (!running && socket === undefined) {
      return;
    }

    running = false;
    clearTimers();
    reconnectAttempts = 0;
    disconnect();
  };

  return {
    start,
    stop,
    isConnected: () => connected,
  };
}
