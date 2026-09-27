CREATE TABLE risk_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    symbol TEXT,
    limit_type TEXT NOT NULL,
    status TEXT NOT NULL,
    threshold NUMERIC NOT NULL CHECK (threshold > 0),
    warning_threshold NUMERIC NOT NULL CHECK (warning_threshold > 0),
    current_value NUMERIC NOT NULL CHECK (current_value >= 0),
    timestamp TIMESTAMPTZ NOT NULL,

    CHECK (warning_threshold < threshold),

    CHECK (
        event_type IN (
            'RISK_LIMIT_WARNING',
            'RISK_LIMIT_BREACHED'
        )
    ),

    CHECK (
        status IN (
            'warning',
            'breached'
        )
    ),

    CHECK (
        (
            event_type = 'RISK_LIMIT_WARNING'
            AND status = 'warning'
        )
        OR
        (
            event_type = 'RISK_LIMIT_BREACHED'
            AND status = 'breached'
        )
    ),

    CHECK (
        symbol IS NULL
        OR length(trim(symbol)) > 0
    )
);

CREATE INDEX idx_risk_events_symbol_timestamp
    ON risk_events (symbol, timestamp);

CREATE INDEX idx_risk_events_timestamp
    ON risk_events (timestamp);