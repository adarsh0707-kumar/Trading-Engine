export const apiErrorSchema = {
  type: "object",
  additionalProperties: false,
  required: ["error"],
  properties: {
    error: {
      type: "object",
      additionalProperties: false,
      required: ["code", "message", "request_id"],
      properties: {
        code: {
          type: "string",
          enum: [
            "INVALID_ARGUMENT",
            "UNAUTHORIZED",
            "FORBIDDEN",
            "NOT_FOUND",
            "CONFLICT",
            "DEPENDENCY_UNAVAILABLE",
            "INTERNAL_ERROR",
          ],
        },
        message: {
          type: "string",
        },
        request_id: {
          type: "string",
        },
      },
    },
  },
} as const;

export const statusResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["data"],
  properties: {
    data: {
      type: "object",
      additionalProperties: false,
      required: ["gateway", "engine", "analytics"],
      properties: {
        gateway: {
          type: "string",
          enum: ["ok"],
        },
        engine: {
          type: "string",
          enum: ["connected", "disconnected"],
        },
        analytics: {
          type: "string",
          enum: ["connected", "disconnected"],
        },
      },
    },
  },
} as const;

export const marketResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["data"],
  properties: {
    data: {
      type: "object",
      additionalProperties: false,
      required: ["symbol", "lastPrice", "lastQuantity", "timestamp"],
      properties: {
        symbol: { type: "string" },
        lastPrice: { type: "number" },
        lastQuantity: { type: "number" },
        timestamp: { type: "string" },
      },
    },
  },
} as const;

export const orderBookResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["data"],
  properties: {
    data: {
      type: "object",
      additionalProperties: false,
      required: ["symbol", "bids", "asks", "timestamp"],
      properties: {
        symbol: { type: "string" },
        bids: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: ["price", "quantity"],
            properties: {
              price: { type: "number" },
              quantity: { type: "number" },
            },
          },
        },
        asks: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: ["price", "quantity"],
            properties: {
              price: { type: "number" },
              quantity: { type: "number" },
            },
          },
        },
        timestamp: { type: "string" },
      },
    },
  },
} as const;

export const tradesResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["data"],
  properties: {
    data: {
      type: "object",
      additionalProperties: false,
      required: ["trades"],
      properties: {
        trades: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: [
              "tradeId",
              "symbol",
              "price",
              "quantity",
              "takerSide",
              "timestamp",
            ],
            properties: {
              tradeId: { type: "string" },
              symbol: { type: "string" },
              price: { type: "number" },
              quantity: { type: "number" },
              takerSide: {
                type: "string",
                enum: ["buy", "sell"],
              },
              timestamp: { type: "string" },
            },
          },
        },
      },
    },
  },
} as const;

export const analyticsResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["data"],
  properties: {
    data: {
      type: "object",
      additionalProperties: false,
      required: [
        "equity",
        "realizedPnl",
        "unrealizedPnl",
        "drawdown",
        "riskStatus",
        "timestamp",
      ],
      properties: {
        equity: { type: "number" },
        realizedPnl: { type: "number" },
        unrealizedPnl: { type: "number" },
        drawdown: { type: "number" },
        riskStatus: {
          type: "string",
          enum: ["ok", "warning", "breached"],
        },
        timestamp: { type: "string" },
      },
    },
  },
} as const;

export const engineActionResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["data"],
  properties: {
    data: {
      type: "object",
      additionalProperties: false,
      required: ["action", "status"],
      properties: {
        action: {
          type: "string",
          enum: ["start", "stop", "reset"],
        },
        status: {
          type: "string",
          enum: ["accepted"],
        },
      },
    },
  },
} as const;


export const engineHealthResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["data"],
  properties: {
    data: {
      type: "object",
      additionalProperties: false,
      required: [
        "state",
        "connectedAt",
        "lastMessageAt",
        "lastHeartbeatAt",
        "reconnectAttempts",
      ],
      properties: {
        state: {
          type: "string",
          enum: ["connecting", "connected", "disconnected"],
        },
        connectedAt: { type: ["integer", "null"] },
        lastMessageAt: { type: ["integer", "null"] },
        lastHeartbeatAt: { type: ["integer", "null"] },
        reconnectAttempts: { type: "integer", minimum: 0 },
      },
    },
  },
} as const;


export const readinessResponseSchema = {
  type: "object",
  additionalProperties: false,
  required: ["status", "service", "dependencies"],
  properties: {
    status: {
      type: "string",
      enum: ["ready", "not_ready"],
    },
    service: {
      type: "string",
      enum: ["gateway"],
    },
    dependencies: {
      type: "object",
      additionalProperties: false,
      required: ["gateway", "engine", "analytics"],
      properties: {
        gateway: {
          type: "string",
          enum: ["ok"],
        },
        engine: {
          type: "string",
          enum: ["connected", "disconnected"],
        },
        analytics: {
          type: "string",
          enum: ["connected", "disconnected"],
        },
      },
    },
  },
} as const;
