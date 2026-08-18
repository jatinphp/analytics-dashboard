# Pulse - Real-time Analytics Dashboard

A real-time analytics dashboard: **FastAPI WebSockets** stream live events to
a **React/Recharts** frontend, backed by **PostgreSQL** window-function
queries and a **materialized view** for fast historical trends. Redis
pub/sub is wired in as an optional layer for scaling the WebSocket fan-out
across multiple backend instances.

Comes preloaded with a realistic fake-data generator, so it's fully
interactive out of the box - no real event source required.

## Architecture

```
┌─────────────┐   live events   ┌──────────────┐   pub/sub (optional)   ┌────────┐
│ fake_data.py │ ───────────────▶│  FastAPI     │◀──────────────────────▶│ Redis  │
│  generator   │                 │  WebSocket   │                        └────────┘
└──────┬───────┘                 │  /ws/live    │
       │ writes                  └──────┬───────┘
       ▼                                │ pushes JSON
┌─────────────┐   REST (summary/        ▼
│  PostgreSQL │   trends/top)    ┌──────────────┐
│  events      │◀────────────────│   React app   │
│  table       │                 │  (Vite +      │
│              │                 │   Recharts)   │
│ hourly_event_│  refreshed      └──────────────┘
│ stats (MV)   │  every 15s
└─────────────┘
```

- **`events`** - append-only raw fact table. Every page view, click,
  signup, add-to-cart, and purchase lands here.
- **`hourly_event_stats`** - a materialized view that pre-aggregates
  `events` into hourly buckets by event type / page / country / device.
  Refreshed on a timer (`REFRESH MATERIALIZED VIEW CONCURRENTLY`) so trend
  and top-N queries stay fast without ever re-scanning the raw table.
- **Trend endpoint** uses a real SQL window function - a trailing 6-bucket
  `AVG(...) OVER (ORDER BY bucket ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`
  - to compute the moving-average line, not something faked in Python.
- **WebSocket manager** broadcasts directly to connected clients by
  default. Set `REDIS_URL` and it switches to publishing on a Redis
  channel instead, with every backend replica subscribing and forwarding
  to its own local clients - the standard pattern for running this behind
  a load balancer.

## Prerequisites

- Docker + Docker Compose (recommended), **or**
- Python 3.12+, Node 20+, a local PostgreSQL 16, and optionally Redis

## Quick start (Docker Compose)

```bash
docker compose up --build
```

That's it. On first boot the backend:
1. Creates the `events` table and `hourly_event_stats` materialized view.
2. Seeds ~30 days of realistic historical traffic (biased toward daytime
   hours so the trend chart has visible shape).
3. Starts emitting a new live event every ~0.4–1.5s over the WebSocket.

Open **http://localhost:5173** for the dashboard.
Backend API docs (Swagger) at **http://localhost:8000/docs**.

## Manual setup (no Docker)

1. **Start Postgres and (optionally) Redis** locally, then create the
   database:
   ```bash
   createuser analytics --pwprompt   # password: analytics
   createdb analytics -O analytics
   ```

2. **Backend**
   ```bash
   cd backend
   pip install -r requirements.txt --break-system-packages
   cp .env.example .env   # edit DATABASE_URL / REDIS_URL if needed
   uvicorn app.main:app --reload
   ```
   First run seeds historical data automatically - this can take 15–30s
   for the default 30 days × 3,000 events/day. To reseed later without
   restarting the app:
   ```bash
   python seed.py --days 30 --events-per-day 3000
   ```

3. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open **http://localhost:5173**.

## API reference

| Endpoint | Description |
|---|---|
| `GET /api/metrics/summary` | Events today, active users (5m), revenue today, events/min (1h avg) |
| `GET /api/metrics/trends?start=&end=&event_type=&country=&device=` | Hourly time series with moving average |
| `GET /api/metrics/top?dimension=page\|country\|device&limit=` | Top-N breakdown for a dimension |
| `WS /ws/live` | Live event stream - `{"type": "event", "data": {...}}` per message |

## Project structure

```
backend/
  app/
    main.py            FastAPI app, lifespan startup (schema, seed, background tasks)
    config.py           Settings (env-var driven)
    database.py          Async SQLAlchemy engine/session
    models.py             Event ORM model
    schemas.py             Pydantic response models
    websocket_manager.py    Connection tracking + optional Redis pub/sub
    db/init.sql               Materialized view DDL
    routers/
      metrics.py               REST endpoints
      ws.py                      WebSocket endpoint
    services/
      aggregator.py             Window-function trend/top queries, MV refresh loop
      fake_data.py                Historical seeder + live event generator
  seed.py                CLI reseed script
  requirements.txt
  Dockerfile

frontend/
  src/
    App.jsx              Layout, polling, wires the live feed
    api.js                 REST client
    hooks/useLiveFeed.js     WebSocket hook with auto-reconnect
    components/
      LiveTicker.jsx          Signature element: scrolling raw-event feed
      StatCard.jsx
      FilterBar.jsx
      TrendChart.jsx           Recharts area + moving-average line
      TopBreakdown.jsx          Tab-switchable top-N bars
  vite.config.js         Dev-server proxy (configurable for Docker)

docker-compose.yml
```

## Notes

- All values in the fake-data generator (event mix, revenue, traffic
  curve) live in `backend/app/services/fake_data.py` - swap it out for a
  real event ingestion path (e.g. a Kafka consumer) without touching
  anything else; the rest of the app only depends on rows existing in
  `events`.
- The materialized view refresh interval and fake-event pacing are both
  configurable via environment variables in `config.py`.
