import { apiClient } from "./client";

export const {
  getStatus: getGatewayStatus,
  getEngineStatus,
  getMarket,
  getOrderBook,
  getTrades,
  getAnalytics,
} = apiClient;
