const BASE = "/api/metrics";

async function getJSON(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`);
  }
  return res.json();
}

export function getSummary() {
  return getJSON(`${BASE}/summary`);
}

export function getTrends({ start, end, eventType, country, device }) {
  const params = new URLSearchParams();
  if (start) params.set("start", start.toISOString());
  if (end) params.set("end", end.toISOString());
  if (eventType) params.set("event_type", eventType);
  if (country) params.set("country", country);
  if (device) params.set("device", device);
  return getJSON(`${BASE}/trends?${params.toString()}`);
}

export function getTop({ dimension, start, end, limit = 8 }) {
  const params = new URLSearchParams({ dimension, limit: String(limit) });
  if (start) params.set("start", start.toISOString());
  if (end) params.set("end", end.toISOString());
  return getJSON(`${BASE}/top?${params.toString()}`);
}
