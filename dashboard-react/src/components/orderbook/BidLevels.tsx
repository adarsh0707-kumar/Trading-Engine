import type { OrderBookLevel } from "../../types";

interface BidLevelsProps {
  readonly levels: readonly OrderBookLevel[];
  readonly maxLevels?: number;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  }).format(value);
}

export default function BidLevels({ levels, maxLevels = 8 }: BidLevelsProps) {
  const visibleLevels = [...levels]
    .sort((a, b) => b.price - a.price)
    .slice(0, maxLevels);
  const maxQuantity = Math.max(...visibleLevels.map((level) => level.quantity), 0);

  if (visibleLevels.length === 0) {
    return <div className="orderbook-empty-side">No bid levels</div>;
  }

  return (
    <div className="orderbook-levels" aria-label="Bid levels">
      {visibleLevels.map((level) => (
        <div className="orderbook-row orderbook-row-bid" key={`${level.price}-${level.quantity}`}>
          <span className="orderbook-depth" style={{ width: `${maxQuantity ? (level.quantity / maxQuantity) * 100 : 0}%` }} aria-hidden="true" />
          <span className="orderbook-price">{formatNumber(level.price)}</span>
          <span className="orderbook-quantity">{formatNumber(level.quantity)}</span>
        </div>
      ))}
    </div>
  );
}
