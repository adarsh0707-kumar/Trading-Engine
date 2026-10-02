import { Socket, type Socket as NetSocket } from "node:net";

import {
  serializeGatewayTradeMessage,
} from "./analytics-message.ts";
import type {
  GatewayTradeMessage,
} from "./analytics-message.types.ts";
import type {
  NormalizedEngineEventResult,
} from "../engine-protocol/engine-event.ts";

export type AnalyticsClientState =
  | "connecting"
  | "connected"
  | "disconnected";

export interface AnalyticsClientOptions {
  readonly host: string;
  readonly port: number;
  readonly connectTimeoutMs: number;
  readonly reconnectInitialDelayMs: number;
  readonly reconnectMaxDelayMs: number;
  readonly reconnectMaxAttempts: number;
  readonly maxQueueSize: number;
  readonly onError?: (error: Error) => void;
  readonly onStateChange?: (state: AnalyticsClientState) => void;
  readonly socketFactory?: () => NetSocket;
}

export interface AnalyticsClient {
  readonly start: () => void;
  readonly stop: () => void;
  readonly sendTrade: (event: NormalizedEngineEventResult) => boolean;
  readonly isConnected: () => boolean;
  readonly getQueueSize: () => number;
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

function toGatewayTradeMessage(
  event: NormalizedEngineEventResult,
): GatewayTradeMessage {
  return {
    version: 1,
    type: "TRADE",
    eventId: event.eventId,
    requestId: event.requestId,
    timestamp: event.timestamp,
    payload: {
      tradeId: event.tradeId,
      symbol: event.payload.symbol,
      price: event.payload.price,
      quantity: event.payload.quantity,
      takerOrderId: event.payload.takerOrderId,
      makerOrderId: event.payload.makerOrderId,
      takerSide: event.payload.takerSide,
      buyOrderId: event.payload.buyOrderId,
      sellOrderId: event.payload.sellOrderId,
    },
  };
}

export function createAnalyticsClient(
  options: AnalyticsClientOptions,
): AnalyticsClient {
  let socket: NetSocket | undefined;
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let connectTimer: ReturnType<typeof setTimeout> | undefined;
  let running = false;
  let connected = false;
  let reconnectAttempts = 0;
  const queue: Buffer[] = [];

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

  const emitDisconnected = (): void => {
    if (connected) {
      connected = false;
      options.onStateChange?.("disconnected");
    } else {
      options.onStateChange?.("disconnected");
    }
  };

  const disconnect = (): void => {
    emitDisconnected();

    if (socket !== undefined) {
      socket.removeAllListeners();
      socket.destroy();
      socket = undefined;
    }
  };

  const flushQueue = (): void => {
    if (!socket || !connected) {
      return;
    }

    while (queue.length > 0 && socket !== undefined && connected) {
      const message = queue.shift();

      if (message === undefined) {
        return;
      }

      socket.write(message);
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

    reconnectTimer = setTimeout(() => {
      reconnectTimer = undefined;
      connect();
    }, delay);
  };

  const handleClose = (): void => {
    if (connectTimer !== undefined) {
      clearTimeout(connectTimer);
      connectTimer = undefined;
    }

    socket = undefined;
    emitDisconnected();

    if (running) {
      scheduleReconnect();
    }
  };

  function connect(): void {
    if (!running || socket !== undefined) {
      return;
    }

    options.onStateChange?.("connecting");

    const nextSocket = options.socketFactory?.() ?? new Socket();
    socket = nextSocket;

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
      flushQueue();
    });

    nextSocket.once("error", (error) => {
      emitError(error);
    });

    nextSocket.once("close", handleClose);

    connectTimer = setTimeout(() => {
      connectTimer = undefined;

      if (socket !== nextSocket || connected || !running) {
        return;
      }

      emitError(
        new Error(
          `Analytics connection timed out after ${options.connectTimeoutMs}ms`,
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

  const sendTrade = (
    event: NormalizedEngineEventResult,
  ): boolean => {
    const payload = serializeGatewayTradeMessage(
      toGatewayTradeMessage(event),
    );
    const message = frame(payload);

    if (connected && socket !== undefined) {
      socket.write(message);
      return true;
    }

    if (options.maxQueueSize === 0) {
      emitError(
        new Error(
          "Analytics client is disconnected and its outbound queue is disabled",
        ),
      );
      return false;
    }

    if (queue.length >= options.maxQueueSize) {
      emitError(
        new Error(
          `Analytics outbound queue is full at ${options.maxQueueSize} messages`,
        ),
      );
      return false;
    }

    queue.push(message);
    return true;
  };

  return {
    start,
    stop,
    sendTrade,
    isConnected: () => connected,
    getQueueSize: () => queue.length,
  };
}
