export default function StatCard({ label, value, accent, suffix }) {
  return (
    <div className="stat-card">
      <div className="stat-card__label">{label}</div>
      <div className="stat-card__value mono" style={{ color: accent || "var(--text-primary)" }}>
        {value}
        {suffix && <span className="stat-card__suffix">{suffix}</span>}
      </div>
    </div>
  );
}
