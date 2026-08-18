import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

function formatTick(iso, rangeHours) {
  const d = new Date(iso);
  if (rangeHours <= 24) {
    return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString("en-GB", { month: "short", day: "numeric" });
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip__time mono">
        {new Date(label).toLocaleString("en-GB", {
          month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
        })}
      </div>
      <div className="chart-tooltip__row">
        <span>events</span>
        <span className="mono">{p.event_count}</span>
      </div>
      <div className="chart-tooltip__row">
        <span>unique users</span>
        <span className="mono">{p.unique_users}</span>
      </div>
      <div className="chart-tooltip__row">
        <span>revenue</span>
        <span className="mono">${Number(p.revenue).toFixed(2)}</span>
      </div>
      <div className="chart-tooltip__row chart-tooltip__row--muted">
        <span>6h avg</span>
        <span className="mono">{Number(p.moving_avg_events).toFixed(1)}</span>
      </div>
    </div>
  );
}

export default function TrendChart({ data, rangeHours, loading }) {
  if (loading) {
    return <div className="chart-empty">loading trend data…</div>;
  }
  if (!data || data.length === 0) {
    return <div className="chart-empty">no events in this range yet</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <defs>
          <linearGradient id="eventFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--series-sky)" stopOpacity={0.35} />
            <stop offset="100%" stopColor="var(--series-sky)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--border-soft)" vertical={false} />
        <XAxis
          dataKey="bucket"
          tickFormatter={(v) => formatTick(v, rangeHours)}
          stroke="var(--text-faint)"
          tick={{ fill: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
          minTickGap={40}
        />
        <YAxis
          stroke="var(--text-faint)"
          tick={{ fill: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}
          axisLine={false}
          tickLine={false}
          width={40}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="event_count"
          stroke="var(--series-sky)"
          strokeWidth={1.5}
          fill="url(#eventFill)"
        />
        <Line
          type="monotone"
          dataKey="moving_avg_events"
          stroke="var(--accent)"
          strokeWidth={2}
          dot={false}
          strokeDasharray="0"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
