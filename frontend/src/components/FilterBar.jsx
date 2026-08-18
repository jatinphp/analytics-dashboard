const EVENT_TYPES = ["page_view", "click", "add_to_cart", "signup", "purchase"];
const COUNTRIES = ["US", "GB", "DE", "IN", "BR", "JP", "CA", "FR", "AU", "NG"];
const DEVICES = ["desktop", "mobile", "tablet"];
const RANGES = [
  { label: "24h", hours: 24 },
  { label: "7d", hours: 24 * 7 },
  { label: "30d", hours: 24 * 30 },
];

export default function FilterBar({ filters, onChange }) {
  const set = (patch) => onChange({ ...filters, ...patch });

  return (
    <div className="filter-bar">
      <div className="filter-bar__group">
        {RANGES.map((r) => (
          <button
            key={r.label}
            className={`chip ${filters.rangeHours === r.hours ? "chip--active" : ""}`}
            onClick={() => set({ rangeHours: r.hours })}
          >
            {r.label}
          </button>
        ))}
      </div>

      <div className="filter-bar__group">
        <select
          className="select"
          value={filters.eventType ?? ""}
          onChange={(e) => set({ eventType: e.target.value || null })}
        >
          <option value="">All events</option>
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>{t.replace("_", " ")}</option>
          ))}
        </select>

        <select
          className="select"
          value={filters.country ?? ""}
          onChange={(e) => set({ country: e.target.value || null })}
        >
          <option value="">All countries</option>
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <select
          className="select"
          value={filters.device ?? ""}
          onChange={(e) => set({ device: e.target.value || null })}
        >
          <option value="">All devices</option>
          {DEVICES.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
