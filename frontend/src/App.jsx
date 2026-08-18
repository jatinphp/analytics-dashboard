import { useEffect, useState, useCallback } from "react";
import { getSummary, getTrends, getTop } from "./api.js";
import { useLiveFeed } from "./hooks/useLiveFeed.js";
import StatCard from "./components/StatCard.jsx";
import LiveTicker from "./components/LiveTicker.jsx";
import FilterBar from "./components/FilterBar.jsx";
import TrendChart from "./components/TrendChart.jsx";
import TopBreakdown from "./components/TopBreakdown.jsx";

const SUMMARY_POLL_MS = 5000;
const TRENDS_POLL_MS = 15000;

export default function App() {
  const { events, status } = useLiveFeed();

  const [filters, setFilters] = useState({
    rangeHours: 24,
    eventType: null,
    country: null,
    device: null,
  });
  const [topDimension, setTopDimension] = useState("page");

  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [trendsLoading, setTrendsLoading] = useState(true);
  const [top, setTop] = useState([]);
  const [topLoading, setTopLoading] = useState(true);

  // Summary: polled independently of filters -- it's always "right now, unfiltered".
  useEffect(() => {
    let cancelled = false;
    const load = () => getSummary().then((d) => !cancelled && setSummary(d)).catch(() => {});
    load();
    const id = setInterval(load, SUMMARY_POLL_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const loadTrends = useCallback(() => {
    const end = new Date();
    const start = new Date(end.getTime() - filters.rangeHours * 3600 * 1000);
    setTrendsLoading((prev) => (trends.length === 0 ? true : prev));
    getTrends({
      start,
      end,
      eventType: filters.eventType,
      country: filters.country,
      device: filters.device,
    })
      .then((d) => setTrends(d))
      .catch(() => {})
      .finally(() => setTrendsLoading(false));
  }, [filters.rangeHours, filters.eventType, filters.country, filters.device]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setTrendsLoading(true);
    loadTrends();
    const id = setInterval(loadTrends, TRENDS_POLL_MS);
    return () => clearInterval(id);
  }, [loadTrends]);

  useEffect(() => {
    let cancelled = false;
    const end = new Date();
    const start = new Date(end.getTime() - filters.rangeHours * 3600 * 1000);
    setTopLoading(true);
    getTop({ dimension: topDimension, start, end, limit: 8 })
      .then((d) => !cancelled && setTop(d))
      .catch(() => {})
      .finally(() => !cancelled && setTopLoading(false));
    return () => { cancelled = true; };
  }, [topDimension, filters.rangeHours]);

  const statusLabel = { connected: "live", connecting: "connecting…", reconnecting: "reconnecting…" }[status];

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__brand">
          <span className="app-header__mark" data-status={status} />
          <h1>PULSE</h1>
          <span className="app-header__tagline">real-time analytics</span>
        </div>
        <div className="app-header__status mono">{statusLabel}</div>
      </header>

      <LiveTicker events={events} />

      <main className="app-main">
        <section className="stat-row">
          <StatCard
            label="Events today"
            value={summary ? summary.events_today.toLocaleString() : "—"}
          />
          <StatCard
            label="Active users (5m)"
            value={summary ? summary.active_users_5m.toLocaleString() : "—"}
            accent="var(--series-teal)"
          />
          <StatCard
            label="Revenue today"
            value={summary ? `$${summary.revenue_today.toFixed(2)}` : "—"}
            accent="var(--accent)"
          />
          <StatCard
            label="Events / min (1h avg)"
            value={summary ? summary.events_per_min_last_hour.toFixed(1) : "—"}
            accent="var(--series-violet)"
          />
        </section>

        <FilterBar filters={filters} onChange={setFilters} />

        <section className="dashboard-grid">
          <div className="panel panel--chart">
            <div className="panel__header">
              <h2>Event volume</h2>
              <div className="legend">
                <span className="legend__item">
                  <span className="legend__swatch" style={{ background: "var(--series-sky)" }} />
                  events
                </span>
                <span className="legend__item">
                  <span className="legend__swatch" style={{ background: "var(--accent)" }} />
                  6h moving avg
                </span>
              </div>
            </div>
            <TrendChart data={trends} rangeHours={filters.rangeHours} loading={trendsLoading} />
          </div>

          <TopBreakdown
            data={top}
            dimension={topDimension}
            onDimensionChange={setTopDimension}
            loading={topLoading}
          />
        </section>
      </main>
    </div>
  );
}
