CREATE TABLE IF NOT EXISTS trades (
    event_id TEXT NOT NULL, event_type TEXT NOT NULL, trade_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL, price NUMERIC(30,10) NOT NULL, quantity BIGINT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL, taker_side TEXT NOT NULL, buy_order_id TEXT NOT NULL,
    sell_order_id TEXT NOT NULL, taker_order_id TEXT NOT NULL, maker_order_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades(symbol, timestamp, trade_id);

CREATE TABLE IF NOT EXISTS analytics_results (
    event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, symbol TEXT NOT NULL,
    price NUMERIC(30,10) NOT NULL, vwap NUMERIC(30,10), sma NUMERIC(30,10),
    ema NUMERIC(30,10), position BIGINT NOT NULL, realized_pnl NUMERIC(30,10) NOT NULL,
    unrealized_pnl NUMERIC(30,10) NOT NULL, equity NUMERIC(30,10) NOT NULL,
    peak_equity NUMERIC(30,10) NOT NULL, drawdown NUMERIC(30,10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analytics_symbol_timestamp ON analytics_results(symbol, timestamp, event_id);

CREATE TABLE IF NOT EXISTS positions (
    symbol TEXT PRIMARY KEY, position BIGINT NOT NULL, average_entry_price NUMERIC(30,10),
    realized_pnl NUMERIC(30,10) NOT NULL, unrealized_pnl NUMERIC(30,10) NOT NULL,
    equity NUMERIC(30,10) NOT NULL, peak_equity NUMERIC(30,10) NOT NULL,
    drawdown NUMERIC(30,10) NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_state (
    symbol TEXT PRIMARY KEY, position BIGINT NOT NULL, average_entry_price NUMERIC(30,10),
    realized_pnl NUMERIC(30,10) NOT NULL, unrealized_pnl NUMERIC(30,10) NOT NULL,
    equity NUMERIC(30,10) NOT NULL, peak_equity NUMERIC(30,10) NOT NULL,
    drawdown NUMERIC(30,10) NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_events (
    event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, symbol TEXT NOT NULL,
    limit_type TEXT NOT NULL, status TEXT NOT NULL, threshold NUMERIC(30,10) NOT NULL,
    warning_threshold NUMERIC(30,10) NOT NULL, current_value NUMERIC(30,10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_risk_events_symbol_timestamp ON risk_events(symbol, timestamp, event_id);
