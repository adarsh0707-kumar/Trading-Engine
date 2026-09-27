-- Create the derived analytics-result store.
--
-- Analytics results are derived from authoritative trade events.
-- event_id is therefore the stable identifier for idempotent persistence.

CREATE TABLE analytics_results (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL CHECK (event_type = 'ANALYTICS_UPDATE'),
    symbol TEXT NOT NULL,
    price NUMERIC NOT NULL CHECK (price > 0),

    vwap NUMERIC,
    sma NUMERIC,
    ema NUMERIC,

    position BIGINT NOT NULL,

    realized_pnl NUMERIC NOT NULL,
    unrealized_pnl NUMERIC NOT NULL,

    equity NUMERIC NOT NULL,
    peak_equity NUMERIC NOT NULL,

    drawdown NUMERIC NOT NULL CHECK (drawdown >= 0),

    timestamp TIMESTAMPTZ NOT NULL,

    CHECK (peak_equity >= equity)
);

CREATE INDEX idx_analytics_results_symbol_timestamp
    ON analytics_results (symbol, timestamp, event_id);

CREATE INDEX idx_analytics_results_timestamp
    ON analytics_results (timestamp);
