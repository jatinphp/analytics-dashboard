const EVENT_COLOR = {
  page_view: "var(--series-sky)",
  click: "var(--series-violet)",
  add_to_cart: "var(--series-amber)",
  signup: "var(--series-teal)",
  purchase: "var(--series-rose)",
};

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-GB", { hour12: false });
}

export default function LiveTicker({ events }) {
  return (
    <div className="ticker">
      <div className="ticker__rail">
        {events.length === 0 && (
          <span className="ticker__placeholder">waiting for events…</span>
        )}
        {events.map((e, i) => (
          <div className="ticker__item" key={`${e.created_at}-${i}`}>
            <span
              className="ticker__dot"
              style={{ background: EVENT_COLOR[e.event_type] || "var(--text-muted)" }}
            />
            <span className="mono ticker__time">{formatTime(e.created_at)}</span>
            <span className="ticker__type">{e.event_type.replace("_", " ")}</span>
            <span className="ticker__page">{e.page}</span>
            <span className="ticker__meta mono">{e.country} · {e.device}</span>
            {e.revenue > 0 && (
              <span className="ticker__revenue mono">+${e.revenue.toFixed(2)}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
