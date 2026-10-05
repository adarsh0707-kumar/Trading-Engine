import type { Trade } from "../../types";

interface RecentTradesProps {
  readonly trades: readonly Trade[];
  readonly state: "loading" | "ready" | "error";
  readonly error: string | null;
}

function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  }).format(value);
}

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString();
}

export default function RecentTrades({ trades, state, error }: RecentTradesProps) {
  if (state === "loading") {
    return <div className="state-message">Loading recent trades…</div>;
  }

  if (state === "error" && trades.length === 0) {
    return (
      <div className="state-message state-error">
        Trades unavailable{error ? " — " + error : ""}
      </div>
    );
  }

  if (trades.length === 0) {
    return <div className="state-message">No trades available yet.</div>;
  }

  return (
    <div className="trades-table-wrap">
      <table className="trades-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Price</th>
            <th>Quantity</th>
            <th>Trade ID</th>
            <th>Buy Order</th>
            <th>Sell Order</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <tr key={trade.tradeId}>
              <td>{formatTime(trade.timestamp)}</td>
              <td>{trade.symbol}</td>
              <td>
                <span className={"trade-side trade-side-" + trade.takerSide.toLowerCase()}>
                  {trade.takerSide.toUpperCase()}
                </span>
              </td>
              <td>{formatPrice(trade.price)}</td>
              <td>{formatPrice(trade.quantity)}</td>
              <td className="trade-id">{trade.tradeId}</td>
              <td className="trade-id">{trade.buyOrderId ?? "—"}</td>
              <td className="trade-id">{trade.sellOrderId ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
