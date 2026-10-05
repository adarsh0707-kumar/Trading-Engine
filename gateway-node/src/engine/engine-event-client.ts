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

export type EngineClientState = "connecting" | "connected" | "disconnected";

export interface EngineHealth {
  readonly state: EngineClientState;
  readonly connectedAt: number | null;
  readonly lastMessageAt: number | null;
  readonly lastHeartbeatAt: number | null;
  readonly reconnectAttempts: number;
}

export interface EngineEventClientOptions {
  readonly host: string;
  readonly port: number;
  readonly connectTimeoutMs: number;
  readonly heartbeatTimeoutMs?: number;
  readonly reconnectInitialDelayMs: number;
  readonly reconnectMaxDelayMs: number;
  readonly reconnectMaxAttempts: number;
  readonly onEvent: (event: NormalizedEngineEventResult) => void;
  readonly onError?: (error: Error) => void;
  readonly onStateChange?: (state: EngineClientState) => void;
  readonly onHealthEvent?: (event: {
    readonly type:
      | "message"
      | "heartbeat"
      | "reconnect_attempt"
      | "connection_failure"
      | "protocol_failure"
      | "timeout_failure"
      | "liveness_timeout";
    readonly timestamp: number;
  }) => void;
  readonly socketFactory?: () => NetSocket;
  readonly protocolFactory?: () => EngineProtocol;
}

export interface EngineEventClient {
  readonly start: () => void;
  readonly stop: () => void;
  readonly isConnected: () => boolean;
  readonly getState: () => EngineClientState;
  readonly getHealth: () => EngineHealth;
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
  let livenessTimer: ReturnType<typeof setTimeout> | undefined;
  let running = false;
  let connected = false;
  let reconnectAttempts = 0;
  let state: EngineClientState = "disconnected";
  let connectedAt: number | null = null;
  let lastMessageAt: number | null = null;
  let lastHeartbeatAt: number | null = null;

  const clearLivenessTimer = (): void => {
    if (livenessTimer !== undefined) {
      clearTimeout(livenessTimer);
      livenessTimer = undefined;
    }
  };

  const clearTimers = (): void => {
    if (reconnectTimer !== undefined) {
      clearTimeout(reconnectTimer);
      reconnectTimer = undefined;
    }

    if (connectTimer !== undefined) {
      clearTimeout(connectTimer);
      connectTimer = undefined;
    }

    clearLivenessTimer();
  };

  const emitState = (nextState: EngineClientState): void => {
    state = nextState;
    connected = nextState === "connected";
    if (nextState === "connected") {
      connectedAt = Date.now();
    } else if (nextState === "disconnected") {
      connectedAt = null;
      clearLivenessTimer();
    }
    options.onStateChange?.(nextState);
  };

  const emitHealthEvent = (
    type:
      | "message"
      | "heartbeat"
      | "reconnect_attempt"
      | "connection_failure"
      | "protocol_failure"
      | "timeout_failure"
      | "liveness_timeout",
  ): void => {
    options.onHealthEvent?.({ type, timestamp: Date.now() });
  };

  const emitError = (error: unknown): void => {
    options.onError?.(toError(error));
  };

  const emitConnectionError = (error: unknown): void => {
    const normalized = toError(error);
    emitError(
      normalized instanceof ConnectionFailure
        ? normalized
        : new ConnectionFailure(normalized.message),
    );
  };

  const scheduleLivenessTimeout = (nextSocket: NetSocket): void => {
    clearLivenessTimer();

    const timeoutMs = options.heartbeatTimeoutMs ?? 0;
    if (timeoutMs <= 0 || !running || socket !== nextSocket) {
      return;
    }

    livenessTimer = setTimeout(() => {
      livenessTimer = undefined;

      if (!running || socket !== nextSocket || !connected) {
        return;
      }

      emitError(
        new TimeoutFailure(
          `Engine heartbeat liveness timed out after ${timeoutMs}ms`,
        ),
      );
      emitHealthEvent("liveness_timeout");
      nextSocket.destroy();
    }, timeoutMs);
  };

  const disconnect = (): void => {
    clearLivenessTimer();

    if (state !== "disconnected") {
      emitState("disconnected");
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
      options.reconnectInitialDelayMs * 2 ** reconnectAttempts,
      options.reconnectMaxDelayMs,
    );

    reconnectAttempts += 1;
    emitHealthEvent("reconnect_attempt");

    reconnectTimer = setTimeout(() => {
      reconnectTimer = undefined;
      connect();
    }, delay);
  };

  const handleClose = (
    closedSocket: NetSocket,
    closedProtocol: EngineProtocol,
  ): void => {
    if (connectTimer !== undefined) {
      clearTimeout(connectTimer);
      connectTimer = undefined;
    }

    if (socket !== closedSocket) return;

    clearLivenessTimer();
    emitState("disconnected");
    socket = undefined;

    closedProtocol.reset();

    if (running) {
      scheduleReconnect();
    }
  };

  const handleData = (
    nextSocket: NetSocket,
    nextProtocol: EngineProtocol,
    chunk: Buffer,
  ): void => {
    try {
      const messages = nextProtocol.push(
        new Uint8Array(
          chunk.buffer,
          chunk.byteOffset,
          chunk.byteLength,
        ),
      );

      for (const message of messages) {
        lastMessageAt = Date.now();
        emitHealthEvent("message");

        if (message.type === "HEARTBEAT") {
          lastHeartbeatAt = lastMessageAt;
          emitHealthEvent("heartbeat");
          scheduleLivenessTimeout(nextSocket);

          if (socket !== nextSocket) return;
          nextSocket.write(
            heartbeatResponse(
              message.requestId,
              message.timestamp,
            ),
          );
          continue;
        }

        if (message.type === "HELLO") {
          // The C++ engine sends HELLO immediately after accepting a client.
          // It is a transport-level control message, not a trade event.
          continue;
        }

        if (message.type !== "TRADE") {
          continue;
        }

        options.onEvent(normalizeEngineEvent(message));
      }
    } catch (error) {
      const normalized = toError(error);
      const protocolError =
        normalized instanceof ProtocolFailure
          ? normalized
          : new ProtocolFailure(normalized.message);
      emitError(protocolError);
      emitHealthEvent("protocol_failure");
      if (socket === nextSocket) nextSocket.destroy();
    }
  };

  function connect(): void {
    if (!running || socket !== undefined) {
      return;
    }

    emitState("connecting");

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

      emitState("connected");
      reconnectAttempts = 0;
      scheduleLivenessTimeout(nextSocket);
    });

    nextSocket.on("data", (chunk) =>
      handleData(nextSocket, nextProtocol, Buffer.from(chunk)),
    );

    nextSocket.once("error", (error) => {
      if (socket === nextSocket) {
        emitConnectionError(error);
        emitHealthEvent("connection_failure");
      }
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
      emitHealthEvent("timeout_failure");

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
    getState: () => state,
    getHealth: () => ({
      state,
      connectedAt,
      lastMessageAt,
      lastHeartbeatAt,
      reconnectAttempts,
    }),
  };
}
