import type { AnalyticsHistoryPoint } from "../../hooks/useAnalytics";

export interface AnalyticsSeries {
  readonly key: keyof AnalyticsHistoryPoint;
  readonly label: string;
  readonly stroke: "orange" | "cream" | "chocolate";
}

interface AnalyticsChartProps {
  readonly points: readonly AnalyticsHistoryPoint[];
  readonly series: readonly AnalyticsSeries[];
  readonly title: string;
  readonly valueFormatter?: (value: number) => string;
  readonly emptyMessage?: string;
}

const WIDTH = 900;
const HEIGHT = 280;
const PAD_X = 44;
const PAD_Y = 24;

function numericValues(points: readonly AnalyticsHistoryPoint[], key: keyof AnalyticsHistoryPoint): number[] {
  return points.flatMap((point) => {
    const value = point[key];
    return typeof value === "number" && Number.isFinite(value) ? [value] : [];
  });
}

function pathFor(points: readonly AnalyticsHistoryPoint[], key: keyof AnalyticsHistoryPoint, min: number, max: number): string {
  const values = points.map((point) => point[key]);
  const range = max - min || 1;
  const xStep = points.length > 1 ? (WIDTH - PAD_X * 2) / (points.length - 1) : 0;
  let path = "";
  let drawing = false;

  values.forEach((value, index) => {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      drawing = false;
      return;
    }
    const x = PAD_X + index * xStep;
    const y = HEIGHT - PAD_Y - ((value - min) / range) * (HEIGHT - PAD_Y * 2);
    path += (drawing ? " L" : "M") + " " + x.toFixed(2) + " " + y.toFixed(2);
    drawing = true;
  });

  return path;
}

export default function AnalyticsChart({
  points,
  series,
  title,
  valueFormatter = (value) => value.toFixed(2),
  emptyMessage = "Waiting for analytics updates…",
}: AnalyticsChartProps) {
  const allValues = series.flatMap((item) => numericValues(points, item.key));
  if (allValues.length === 0) {
    return (
      <section className="analytics-chart">
        <div className="section-heading">
          <div>
            <span className="panel-eyebrow">CHART</span>
            <h2>{title}</h2>
          </div>
        </div>
        <div className="state-message analytics-chart-empty">{emptyMessage}</div>
      </section>
    );
  }

  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min || Math.max(Math.abs(max), 1);
  const domainMin = min - range * 0.08;
  const domainMax = max + range * 0.08;

  return (
    <section className="analytics-chart">
      <div className="section-heading">
        <div>
          <span className="panel-eyebrow">CHART</span>
          <h2>{title}</h2>
        </div>
        <span className="stream-state">{points.length} points</span>
      </div>

      <div className="analytics-chart-legend" aria-label="Chart series">
        {series.map((item) => (
          <span key={item.label} className="analytics-chart-legend-item">
            <i className={"analytics-line analytics-line-" + item.stroke} aria-hidden="true" />
            {item.label}
          </span>
        ))}
      </div>

      <div className="analytics-chart-frame">
        <svg className="analytics-chart-svg" viewBox={"0 0 " + WIDTH + " " + HEIGHT} role="img" aria-label={title}>
          <line x1={PAD_X} x2={WIDTH - PAD_X} y1={PAD_Y} y2={PAD_Y} className="analytics-grid-line" />
          <line x1={PAD_X} x2={WIDTH - PAD_X} y1={HEIGHT / 2} y2={HEIGHT / 2} className="analytics-grid-line" />
          <line x1={PAD_X} x2={WIDTH - PAD_X} y1={HEIGHT - PAD_Y} y2={HEIGHT - PAD_Y} className="analytics-grid-line" />
          {series.map((item) => (
            <path
              key={item.label}
              d={pathFor(points, item.key, domainMin, domainMax)}
              className={"analytics-series analytics-series-" + item.stroke}
              fill="none"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}
          <text x={PAD_X} y={HEIGHT - 4} className="analytics-axis-label">
            {points[0] ? new Date(points[0].timestamp).toLocaleTimeString() : ""}
          </text>
          <text x={WIDTH - PAD_X} y={HEIGHT - 4} textAnchor="end" className="analytics-axis-label">
            {points.at(-1) ? new Date(points.at(-1)!.timestamp).toLocaleTimeString() : ""}
          </text>
          <text x={WIDTH - PAD_X} y={PAD_Y - 6} textAnchor="end" className="analytics-axis-label">
            {valueFormatter(domainMax)}
          </text>
          <text x={WIDTH - PAD_X} y={HEIGHT - PAD_Y + 16} textAnchor="end" className="analytics-axis-label">
            {valueFormatter(domainMin)}
          </text>
        </svg>
      </div>
    </section>
  );
}
