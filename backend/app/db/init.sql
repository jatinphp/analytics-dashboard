-- Materialized view: pre-aggregates raw events into hourly buckets so
-- trend/top-N queries stay fast even as the events table grows into the
-- millions of rows. Refreshed on a timer by a background task
-- (see app/services/aggregator.py) rather than on every query.

CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_event_stats AS
SELECT
    date_trunc('hour', created_at)  AS bucket,
    event_type,
    page,
    country,
    device,
    COUNT(*)                        AS event_count,
    COUNT(DISTINCT user_id)         AS unique_users,
    COALESCE(SUM(revenue), 0)       AS revenue
FROM events
GROUP BY 1, 2, 3, 4, 5
WITH NO DATA;

-- A unique index on the grouping columns is required for
-- REFRESH MATERIALIZED VIEW CONCURRENTLY, which lets us refresh the view
-- without blocking reads against it.
CREATE UNIQUE INDEX IF NOT EXISTS hourly_event_stats_unique_idx
    ON hourly_event_stats (bucket, event_type, page, country, device);

-- Populate it once at init time so the first refresh is CONCURRENTLY-safe.
REFRESH MATERIALIZED VIEW hourly_event_stats;
