#!/usr/bin/env bash
set -Eeuo pipefail

# Deterministically seed one valid but unacknowledged TRADE frame into the
# persistent SQLite outbox while the gateway process is stopped, then prove
# that a gateway restart delivers it to the real analytics/PostgreSQL stack.
event_id="outbox-restart-e2e-$(date -u +%Y%m%dT%H%M%S)-${GITHUB_RUN_ATTEMPT:-1}"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
gateway_ready_url="http://127.0.0.1:${GATEWAY_PORT:-8080}/api/health"

cleanup() {
  docker compose start gateway >/dev/null 2>&1 || true
}
trap cleanup EXIT

inject_pending_trade() {
  docker compose run --rm --no-deps \
    -e "E2E_EVENT_ID=$event_id" \
    -e "E2E_TIMESTAMP=$timestamp" \
    gateway bun -e '
      import { SqliteTradeOutbox } from "./src/analytics/trade-outbox.ts";

      const eventId = process.env.E2E_EVENT_ID;
      const timestamp = process.env.E2E_TIMESTAMP;
      const path = process.env.GATEWAY_TRADE_OUTBOX_PATH;
      if (!eventId || !timestamp || !path) {
        throw new Error("missing outbox E2E environment");
      }

      const message = {
        version: 1,
        type: "TRADE",
        event_id: eventId,
        request_id: eventId,
        timestamp,
        payload: JSON.stringify({
          trade_id: eventId,
          symbol: "SIM",
          price: 100.25,
          quantity: 1,
          taker_order_id: eventId + "-buy",
          maker_order_id: eventId + "-sell",
          taker_side: "BUY",
          buy_order_id: eventId + "-buy",
          sell_order_id: eventId + "-sell"
        })
      };
      const body = Buffer.from(JSON.stringify(message), "utf8");
      const framed = Buffer.alloc(4 + body.length);
      framed.writeUInt32BE(body.length, 0);
      body.copy(framed, 4);

      const outbox = new SqliteTradeOutbox(path);
      try {
        outbox.enqueue(eventId, framed);
      } finally {
        outbox.close();
      }
      console.log("Seeded one durable unacknowledged trade:", eventId);
    '
}

trade_count() {
  docker compose exec -T postgres psql \
    -U trading_engine -d trading_engine -tAc \
    "SELECT COUNT(*) FROM public.trades WHERE trade_id = '$event_id';" |
    tr -d '[:space:]'
}

outbox_count() {
  docker compose exec -T gateway bun -e '
    import { Database } from "bun:sqlite";
    const path = process.env.GATEWAY_TRADE_OUTBOX_PATH;
    if (!path) throw new Error("GATEWAY_TRADE_OUTBOX_PATH is unset");
    const db = new Database(path, { readonly: true });
    try {
      const row = db.query("SELECT COUNT(*) AS count FROM analytics_trade_outbox").get();
      console.log(row.count);
    } finally {
      db.close();
    }
  ' | tr -d '[:space:]'
}

echo "=== Seed durable pending trade while gateway is stopped ==="
docker compose stop gateway
inject_pending_trade

echo "=== Restart gateway and wait for PostgreSQL persistence + ACK cleanup ==="
docker compose start gateway
for attempt in $(seq 1 60); do
  if curl --fail --silent "$gateway_ready_url" >/dev/null; then
    persisted="$(trade_count)"
    pending="$(outbox_count)"
    echo "attempt=$attempt persisted_rows=$persisted outbox_rows=$pending"
    if [[ "$persisted" == "1" && "$pending" == "0" ]]; then
      break
    fi
  fi
  sleep 2
done

persisted="$(trade_count)"
pending="$(outbox_count)"
if [[ "$persisted" != "1" || "$pending" != "0" ]]; then
  echo "ERROR: durable replay did not converge (rows=$persisted, outbox=$pending)" >&2
  docker compose logs --no-color gateway analytics
  exit 1
fi

echo "PASS: gateway restart replayed $event_id; PostgreSQL has exactly one row and the outbox is empty."
