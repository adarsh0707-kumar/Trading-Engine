# Data Model and Event Contracts

## 1. Purpose

This document defines the logical data model exchanged between the C++ engine, Python analytics service, Node gateway, and React dashboard.

The model is designed to be transport-independent. JSON is used for the MVP, while the same schema can later be represented using Protocol Buffers.

---

## 2. Identifier Rules

All externally visible events should have:

- `event_id`
- `timestamp`
- `event_type`

Orders have:

- `order_id`
- `client_order_id` where relevant

Identifiers must be unique within the simulation session.

Recommended format:

```text
evt-000001
ord-000001
trd-000001
```

---

## 3. Enumerations

### Order side

```text
BUY
SELL
```

### Order type

```text
LIMIT
MARKET
```

The MVP may implement LIMIT only.

### Time in force

```text
GTC
IOC
```

The MVP may implement GTC only.

### Order status

```text
NEW
PARTIALLY_FILLED
FILLED
CANCELLED
REJECTED
```

### Event types

```text
ORDER_ACCEPTED
ORDER_REJECTED
ORDER_CANCELLED
TRADE
BOOK_UPDATE
MARKET_TICK
ANALYTICS_UPDATE
SIMULATION_STATUS
ERROR
```

---

## 4. Order

```json
{
  "order_id": "ord-000001",
  "symbol": "SIM",
  "side": "BUY",
  "type": "LIMIT",
  "price": 101.25,
  "quantity": 100,
  "remaining_quantity": 60,
  "status": "PARTIALLY_FILLED",
  "sequence": 42,
  "timestamp": "2026-09-07T12:00:00.100Z"
}
```

### Validation rules

- Price must be positive for a limit order.
- Quantity must be a positive integer.
- Side must be supported.
- Symbol must be valid.
- Sequence must be monotonically increasing.

---

## 5. Trade

```json
{
  "event_type": "TRADE",
  "event_id": "evt-000123",
  "trade_id": "trd-000045",
  "symbol": "SIM",
  "price": 101.25,
  "quantity": 40,
  "buy_order_id": "ord-000010",
  "sell_order_id": "ord-000009",
  "timestamp": "2026-09-07T12:00:01.000Z"
}
```

The trade event is authoritative for downstream analytics.

---

## 6. Book Level

```json
{
  "price": 101.25,
  "quantity": 250,
  "order_count": 4
}
```

A book snapshot:

```json
{
  "event_type": "BOOK_UPDATE",
  "symbol": "SIM",
  "bids": [
    {"price": 101.00, "quantity": 200, "order_count": 3}
  ],
  "asks": [
    {"price": 101.25, "quantity": 250, "order_count": 4}
  ]
}
```

---

## 7. Market Tick

```json
{
  "event_type": "MARKET_TICK",
  "event_id": "evt-000200",
  "symbol": "SIM",
  "price": 101.20,
  "quantity": 15,
  "timestamp": "2026-09-07T12:00:02.000Z"
}
```

---

## 8. Analytics Event

```json
{
  "event_type": "ANALYTICS_UPDATE",
  "event_id": "evt-000201",
  "symbol": "SIM",
  "price": 101.20,
  "vwap": 101.13,
  "sma": 101.10,
  "ema": 101.16,
  "position": 150,
  "realized_pnl": 120.00,
  "unrealized_pnl": 64.50,
  "equity": 10184.50,
  "peak_equity": 10210.00,
  "drawdown": 25.50,
  "timestamp": "2026-09-07T12:00:02.000Z"
}
```

---

## 9. Simulation Status

```json
{
  "event_type": "SIMULATION_STATUS",
  "state": "RUNNING",
  "events_processed": 125000,
  "events_per_second": 18500,
  "timestamp": "2026-09-07T12:00:05.000Z"
}
```

---

## 10. VWAP

For a window of trades:

\[
VWAP = \frac{\sum(P_i Q_i)}{\sum Q_i}
\]

where:

- `P_i` = trade price
- `Q_i` = trade quantity

The implementation must avoid integer division.

---

## 11. SMA

For N observations:

\[
SMA_N = \frac{x_1+x_2+\cdots+x_N}{N}
\]

A rolling queue should be used rather than recomputing the complete history for every event.

---

## 12. EMA

A standard EMA can use:

\[
EMA_t = \alpha P_t + (1-\alpha)EMA_{t-1}
\]

where:

\[
\alpha = \frac{2}{N+1}
\]

The chosen initialization rule must be documented and tested.

---

## 13. Position Model

A simplified position can be represented as:

```text
position = cumulative_buy_quantity - cumulative_sell_quantity
```

Example:

```text
BUY 100
SELL 30
BUY 50

position = 120
```

---

## 14. PnL

For a simplified mark-to-market model:

```text
unrealized_pnl =
    position * (current_price - average_entry_price)
```

Realized PnL depends on the chosen accounting method. The MVP should document whether it uses FIFO, weighted average cost, or another deterministic method.

---

## 15. Risk Model

Initial metrics:

- Gross exposure.
- Net exposure.
- Position size.
- Equity.
- Peak equity.
- Drawdown.
- Maximum drawdown.

Drawdown:

\[
Drawdown = PeakEquity - CurrentEquity
\]

Percentage drawdown:

\[
Drawdown\% =
\frac{PeakEquity-CurrentEquity}{PeakEquity}\times100
\]

---

## 16. Versioning

Every event contract should include a schema version when the protocol becomes externally consumed.

Example:

```json
{
  "schema_version": "1.0",
  "event_type": "TRADE"
}
```

Backward-incompatible changes require a new major version.

---

## 17. Serialization Rules

JSON rules:

- UTF-8.
- Length-prefixed JSON frames for socket streams: a 4-byte big-endian payload length followed by the JSON payload.
- No comments.
- Numeric fields must remain numeric.
- Timestamps use ISO-8601 UTC.
- Unknown fields should be ignored by tolerant consumers where safe.

---

## 18. Protobuf Migration

A future `.proto` model should represent:

- enums,
- order,
- trade,
- book update,
- analytics update,
- simulation status.

The logical field names should remain stable so that migration does not change business semantics.
