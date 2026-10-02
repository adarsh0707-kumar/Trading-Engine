export const ENGINE_MESSAGE_TYPES = [
  "HELLO",
  "HEARTBEAT",
  "ORDER",
  "TRADE",
  "MARKET_DATA",
  "BOOK_SNAPSHOT",
  "ERROR",
  "SHUTDOWN",
] as const;

export type EngineMessageType =
  (typeof ENGINE_MESSAGE_TYPES)[number];

export interface EngineMessage {
  readonly type: EngineMessageType;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: string;
}

export interface NormalizedEngineEvent {
  readonly type: EngineMessageType;
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: string;
}
