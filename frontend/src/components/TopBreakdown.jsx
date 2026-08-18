import { useState } from "react";

const DIMENSIONS = [
  { key: "page", label: "Pages" },
  { key: "country", label: "Countries" },
  { key: "device", label: "Devices" },
];

export default function TopBreakdown({ data, dimension, onDimensionChange, loading }) {
  const maxCount = Math.max(1, ...(data || []).map((d) => d.event_count));

  return (
    <div className="panel">
      <div className="panel__tabs">
        {DIMENSIONS.map((d) => (
          <button
            key={d.key}
            className={`tab ${dimension === d.key ? "tab--active" : ""}`}
            onClick={() => onDimensionChange(d.key)}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="top-list">
        {loading && <div className="chart-empty">loading…</div>}
        {!loading && (!data || data.length === 0) && (
          <div className="chart-empty">no data in this range</div>
        )}
        {!loading && data?.map((item) => (
          <div className="top-list__row" key={item.label}>
            <div className="top-list__label">{item.label}</div>
            <div className="top-list__bar-track">
              <div
                className="top-list__bar-fill"
                style={{ width: `${(item.event_count / maxCount) * 100}%` }}
              />
            </div>
            <div className="top-list__count mono">{item.event_count.toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
