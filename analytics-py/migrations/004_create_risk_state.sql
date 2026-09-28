CREATE TABLE risk_state (
    symbol TEXT PRIMARY KEY,
    position BIGINT NOT NULL,
    average_entry_price NUMERIC,
    realized_pnl NUMERIC NOT NULL,
    unrealized_pnl NUMERIC NOT NULL,
    equity NUMERIC NOT NULL,
    peak_equity NUMERIC NOT NULL,
    drawdown NUMERIC NOT NULL CHECK (drawdown >= 0),

    CHECK (peak_equity >= equity),

    CHECK (
        position = 0
        OR average_entry_price IS NOT NULL
    ),

    CHECK (
        position <> 0
        OR average_entry_price IS NULL
    )
);