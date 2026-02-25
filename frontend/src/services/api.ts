import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Portfolio {
  id: number;
  name: string;
  initial_capital: string;
  cash_balance: string;
  total_value: string;
  total_pnl: string;
  total_pnl_pct: number;
  positions_count: number;
  created_at: string;
  updated_at: string;
}

export interface Position {
  id: number;
  symbol: string;
  asset_type: string;
  quantity: string;
  avg_cost_price: string;
  current_price: string;
  market_value: string;
  unrealized_pnl: string;
  unrealized_pnl_pct: number;
  realized_pnl: string;
  weight_pct: number;
}

export interface Order {
  id: number;
  portfolio: number;
  symbol: string;
  asset_type: string;
  side: "BUY" | "SELL";
  order_type: string;
  quantity: string;
  limit_price: string | null;
  stop_price: string | null;
  status: string;
  source: string;
  ai_recommendation: number | null;
  executed_at: string | null;
  executed_price: string | null;
  rejection_reason: string;
  total_value: number | null;
  created_at: string;
}

export interface Trade {
  id: number;
  order: number;
  portfolio: number;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: string;
  price: string;
  commission: string;
  portfolio_balance_after: string;
  total_value: string;
  executed_at: string;
}

export interface AIRecommendation {
  id: number;
  portfolio: number;
  provider: string;
  symbol: string;
  asset_type: string;
  action: "BUY" | "SELL" | "HOLD" | "REBALANCE";
  confidence: string;
  confidence_pct: number;
  quantity_suggested: string;
  price_target: string | null;
  stop_loss: string | null;
  take_profit: string | null;
  reasoning: string;
  status: string;
  created_at: string;
  expires_at: string | null;
}

export interface StrategyConfig {
  id: number;
  portfolio: number;
  ai_providers: string[];
  strategies: string[];
  risk_tolerance: string;
  max_position_size_pct: string;
  analysis_interval_minutes: number;
  watchlist: string[];
  is_active: boolean;
}

export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  market_cap: number | null;
  timestamp: string;
  source: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ─── Portfolio API ────────────────────────────────────────────────────────────

export const portfolioApi = {
  list: () => api.get<PaginatedResponse<Portfolio>>("/portfolio/"),
  get: (id: number) => api.get<Portfolio>(`/portfolio/${id}/`),
  create: (data: { name: string; initial_capital: string }) =>
    api.post<Portfolio>("/portfolio/", data),
  positions: (id: number) =>
    api.get<PaginatedResponse<Position>>(`/portfolio/${id}/positions/`),
  pnl: (id: number, period = "30d") =>
    api.get<{ period: string; data: { date: string; portfolio_value: number; daily_pnl: number }[] }>(
      `/portfolio/${id}/pnl/?period=${period}`
    ),
  metrics: (id: number) =>
    api.get<Record<string, number>>(`/portfolio/${id}/metrics/`),
};

// ─── Trading API ──────────────────────────────────────────────────────────────

export const tradingApi = {
  listOrders: (params?: { portfolio_id?: number; status?: string }) =>
    api.get<PaginatedResponse<Order>>("/orders/", { params }),
  createOrder: (data: {
    portfolio_id: number;
    symbol: string;
    side: string;
    quantity: string;
    order_type?: string;
    asset_type?: string;
    limit_price?: string;
    stop_price?: string;
  }) => api.post<Order>("/orders/", data),
  approveOrder: (id: number) => api.post<Order>(`/orders/${id}/approve/`),
  rejectOrder: (id: number, reason = "") =>
    api.post<Order>(`/orders/${id}/reject/`, { reason }),
  cancelOrder: (id: number) => api.post<Order>(`/orders/${id}/cancel/`),
  listTrades: (params?: { portfolio_id?: number }) =>
    api.get<PaginatedResponse<Trade>>("/trades/", { params }),
};

// ─── Market Data API ──────────────────────────────────────────────────────────

export const marketApi = {
  quote: (symbol: string) => api.get<Quote>(`/market/quote/${symbol}/`),
  history: (symbol: string, period = "90d") =>
    api.get<{ symbol: string; period: string; data: unknown[] }>(
      `/market/history/${symbol}/?period=${period}`
    ),
};

// ─── AI Advisor API ───────────────────────────────────────────────────────────

export const aiApi = {
  listRecommendations: (params?: {
    portfolio_id?: number;
    status?: string;
    provider?: string;
  }) => api.get<PaginatedResponse<AIRecommendation>>("/recommendations/", { params }),
  approve: (id: number) =>
    api.post<AIRecommendation>(`/recommendations/${id}/approve/`),
  reject: (id: number) =>
    api.post<AIRecommendation>(`/recommendations/${id}/reject/`),
  runAnalysis: (portfolio_id: number) =>
    api.post("/recommendations/run_analysis/", { portfolio_id }),
  getStrategy: (portfolio_id: number) =>
    api.get<PaginatedResponse<StrategyConfig>>(`/strategy/?portfolio_id=${portfolio_id}`),
  updateStrategy: (id: number, data: Partial<StrategyConfig>) =>
    api.patch<StrategyConfig>(`/strategy/${id}/`, data),
  createStrategy: (data: Partial<StrategyConfig>) =>
    api.post<StrategyConfig>("/strategy/", data),
};

// ─── Analytics API ────────────────────────────────────────────────────────────

export const analyticsApi = {
  pnl: (portfolio_id: number, period = "30d") =>
    api.get<{
      data: { date: string; portfolio_value: number; daily_pnl: number }[];
    }>(`/analytics/${portfolio_id}/pnl/?period=${period}`),
  metrics: (portfolio_id: number) =>
    api.get<Record<string, number>>(`/analytics/${portfolio_id}/metrics/`),
};

export default api;
