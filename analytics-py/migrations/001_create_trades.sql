-- Create the authoritative trade-event store.

CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL CHECK (event_type = 'TRADE'),
    symbol TEXT NOT NULL,
    price NUMERIC NOT NULL CHECK (price > 0),
    quantity BIGINT NOT NULL CHECK (quantity > 0),
    timestamp TIMESTAMPTZ NOT NULL,
    taker_side TEXT NOT NULL CHECK (taker_side IN ('BUY', 'SELL')),
    buy_order_id TEXT,
    sell_order_id TEXT,
    taker_order_id TEXT,
    maker_order_id TEXT
);

CREATE INDEX idx_trades_symbol_timestamp
    ON trades (symbol, timestamp, trade_id);

CREATE INDEX idx_trades_timestamp
    ON trades (timestamp);
