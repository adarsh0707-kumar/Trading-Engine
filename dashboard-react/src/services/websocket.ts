import {
  GATEWAY_WEBSOCKET_EVENT_TYPES,
  type GatewayWebSocket,
  type GatewayWebSocketClient,
  type GatewayWebSocketError,
  type GatewayWebSocketEvent,
  type GatewayWebSocketEventType,
  type GatewayWebSocketOptions,
  type GatewayWebSocketState,
} from "../types/websocket";

const OPEN = 1;
const DEFAULT_BASE_URL = "";
const DEFAULT_PATH = "/ws";
const DEFAULT_RECONNECT_INITIAL_DELAY_MS = 250;
const DEFAULT_RECONNECT_MAX_DELAY_MS = 5_000;
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 10;

type JsonRecord = Record<string, unknown>;

function resolveWebSocketUrl(baseUrl: string | undefined, path: string): string {
  const configured = baseUrl ?? import.meta.env.VITE_GATEWAY_WS_URL ?? DEFAULT_BASE_URL;
  const trimmed = configured.replace(/\/+$/, "");
  const protocolUrl = trimmed.startsWith("https://")
    ? `wss://${trimmed.slice("https://".length)}`
    : trimmed.startsWith("http://")
      ? `ws://${trimmed.slice("http://".length)}`
      : trimmed;
  return `${protocolUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null;
}

function isEventType(value: unknown): value is GatewayWebSocketEventType {
  return typeof value === "string" &&
    (GATEWAY_WEBSOCKET_EVENT_TYPES as readonly string[]).includes(value);
}

function isGatewayEvent(value: unknown): value is GatewayWebSocketEvent {
  if (!isRecord(value) || !isEventType(value.type)) return false;
  return typeof value.eventId === "string" &&
    typeof value.requestId === "string" &&
    typeof value.timestamp === "string" &&
    isRecord(value.payload);
}

function parseServerMessage(
  data: unknown,
): GatewayWebSocketEvent | GatewayWebSocketError | null {
  if (typeof data !== "string") {
    return { code: "INVALID_MESSAGE", message: "Gateway WebSocket message must be a JSON string" };
  }

  let value: unknown;
  try {
    value = JSON.parse(data);
  } catch {
    return { code: "INVALID_MESSAGE", message: "Gateway WebSocket message contains invalid JSON" };
  }

  if (!isRecord(value) || typeof value.type !== "string") {
    return { code: "INVALID_MESSAGE", message: "Gateway WebSocket message must contain a type" };
  }

  if (value.type === "CONNECTION_READY" || value.type === "SUBSCRIPTION_UPDATED") {
    return null;
  }

  if (value.type === "ERROR") {
    const error = isRecord(value.error) ? value.error : {};
    return {
      code: typeof error.code === "string" ? error.code : "GATEWAY_ERROR",
      message: typeof error.message === "string"
        ? error.message
        : "Gateway WebSocket reported an error",
    };
  }

  if (!isGatewayEvent(value)) {
    return {
      code: "INVALID_MESSAGE",
      message: "Gateway WebSocket event does not match the expected contract",
    };
  }

  return value;
}

export function createGatewayWebSocketClient(
  options: GatewayWebSocketOptions = {},
): GatewayWebSocketClient {
  const path = options.path ?? DEFAULT_PATH;
  const reconnectEnabled = options.reconnect ?? true;
  const maxReconnectAttempts = options.maxReconnectAttempts ?? DEFAULT_MAX_RECONNECT_ATTEMPTS;
  const reconnectInitialDelayMs = options.reconnectInitialDelayMs ?? DEFAULT_RECONNECT_INITIAL_DELAY_MS;
  const reconnectMaxDelayMs = options.reconnectMaxDelayMs ?? DEFAULT_RECONNECT_MAX_DELAY_MS;
  const webSocketFactory = options.webSocketFactory ??
    ((url: string) => new WebSocket(url) as unknown as GatewayWebSocket);

  const url = resolveWebSocketUrl(options.baseUrl, path);
  const subscriptions = new Set<GatewayWebSocketEventType>();

  let socket: GatewayWebSocket | null = null;
  let state: GatewayWebSocketState = "idle";
  let reconnectAttempts = 0;
  let reconnectTimer: ReturnType<typeof globalThis.setTimeout> | undefined;
  let manuallyClosed = false;

  const setState = (next: GatewayWebSocketState): void => {
    state = next;
    options.onStateChange?.(next);
  };

  const reportError = (error: GatewayWebSocketError): void => {
    options.onError?.(error);
  };

  const sendSubscription = (
    action: "subscribe" | "unsubscribe",
    events: readonly GatewayWebSocketEventType[],
  ): void => {
    if (socket === null || socket.readyState !== OPEN || events.length === 0) return;
    socket.send(JSON.stringify({ action, events }));
  };

  const sendAllSubscriptions = (): void => {
    if (subscriptions.size === 0) return;
    sendSubscription("subscribe", [...subscriptions]);
  };

  const scheduleReconnect = (): void => {
    if (manuallyClosed || !reconnectEnabled || reconnectAttempts >= maxReconnectAttempts) {
      setState("closed");
      return;
    }

    reconnectAttempts += 1;
    const delay = Math.min(
      reconnectInitialDelayMs * 2 ** (reconnectAttempts - 1),
      reconnectMaxDelayMs,
    );

    setState("reconnecting");
    reconnectTimer = globalThis.setTimeout(() => {
      reconnectTimer = undefined;
      if (!manuallyClosed) {
        setState("connecting");
        openSocket();
      }
    }, delay);
  };

  function openSocket(): void {
    try {
      const nextSocket = webSocketFactory(url);
      socket = nextSocket;

      nextSocket.onopen = () => {
        reconnectAttempts = 0;
        setState("open");
        sendAllSubscriptions();
      };

      nextSocket.onmessage = (event) => {
        const message = parseServerMessage(event.data);
        if (message === null) return;
        if ("code" in message) {
          reportError(message);
          return;
        }
        options.onEvent?.(message);
      };

      nextSocket.onerror = () => {
        reportError({
          code: "CONNECTION_ERROR",
          message: "Gateway WebSocket connection failed",
        });
      };

      nextSocket.onclose = () => {
        if (socket === nextSocket) socket = null;
        if (!manuallyClosed) scheduleReconnect();
        else setState("closed");
      };
    } catch (error) {
      reportError({
        code: "CONNECTION_ERROR",
        message: error instanceof Error ? error.message : "Gateway WebSocket connection failed",
      });
      scheduleReconnect();
    }
  }

  const connect = (): void => {
    if (state === "connecting" || state === "open" || state === "reconnecting") return;

    manuallyClosed = false;
    reconnectAttempts = 0;

    if (reconnectTimer !== undefined) {
      globalThis.clearTimeout(reconnectTimer);
      reconnectTimer = undefined;
    }

    setState("connecting");
    openSocket();
  };

  const disconnect = (): void => {
    manuallyClosed = true;

    if (reconnectTimer !== undefined) {
      globalThis.clearTimeout(reconnectTimer);
      reconnectTimer = undefined;
    }

    const currentSocket = socket;
    socket = null;

    if (currentSocket !== null) {
      currentSocket.onopen = null;
      currentSocket.onmessage = null;
      currentSocket.onerror = null;
      currentSocket.onclose = null;
      currentSocket.close();
    }

    setState("closed");
  };

  const subscribe = (events: readonly GatewayWebSocketEventType[]): void => {
    const uniqueEvents = [...new Set(events)].filter(isEventType);
    for (const event of uniqueEvents) subscriptions.add(event);
    sendSubscription("subscribe", uniqueEvents);
  };

  const unsubscribe = (events: readonly GatewayWebSocketEventType[]): void => {
    const uniqueEvents = [...new Set(events)].filter(isEventType);
    for (const event of uniqueEvents) subscriptions.delete(event);
    sendSubscription("unsubscribe", uniqueEvents);
  };

  return {
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    getState: () => state,
  };
}

export type { GatewayWebSocketEvent, GatewayWebSocketEventType };
