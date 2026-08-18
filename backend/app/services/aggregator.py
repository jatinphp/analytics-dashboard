import asyncio
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal

logger = logging.getLogger("aggregator")


async def get_summary(db: AsyncSession) -> dict:
    """
    Headline numbers for the top stat cards. Queried straight off the raw
    events table (cheap enough at this grain) rather than the materialized
    view, so it reflects data up to the second.
    """
    result = await db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE created_at >= date_trunc('day', now()))
                    AS events_today,
                COUNT(DISTINCT user_id) FILTER (
                    WHERE created_at >= now() - interval '5 minutes'
                ) AS active_users_5m,
                COALESCE(SUM(revenue) FILTER (
                    WHERE created_at >= date_trunc('day', now())
                ), 0) AS revenue_today,
                COALESCE(
                    COUNT(*) FILTER (
                        WHERE created_at >= now() - interval '1 hour'
                    ) / 60.0,
                    0
                ) AS events_per_min_last_hour
            FROM events
            """
        )
    )
    row = result.mappings().one()
    return dict(row)


async def get_trends(
    db: AsyncSession,
    *,
    start: datetime,
    end: datetime,
    event_type: str | None,
    country: str | None,
    device: str | None,
) -> list[dict]:
    """
    Hourly time series with a trailing 6-bucket moving average, computed
    with a window function over the materialized view. The moving average
    is what turns a noisy bar-by-bar count into a readable trend line.
    """
    query = text(
        """
        WITH bucketed AS (
            SELECT
                bucket,
                SUM(event_count)        AS event_count,
                SUM(unique_users)       AS unique_users,
                SUM(revenue)            AS revenue
            FROM hourly_event_stats
            WHERE bucket BETWEEN :start AND :end
              AND (CAST(:event_type AS text) IS NULL OR event_type = CAST(:event_type AS text))
              AND (CAST(:country AS text) IS NULL OR country = CAST(:country AS text))
              AND (CAST(:device AS text) IS NULL OR device = CAST(:device AS text))
            GROUP BY bucket
        )
        SELECT
            bucket,
            event_count,
            unique_users,
            revenue,
            AVG(event_count) OVER (
                ORDER BY bucket
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) AS moving_avg_events
        FROM bucketed
        ORDER BY bucket
        """
    )
    result = await db.execute(
        query,
        {
            "start": start,
            "end": end,
            "event_type": event_type,
            "country": country,
            "device": device,
        },
    )
    return [dict(r) for r in result.mappings().all()]


async def get_top(
    db: AsyncSession,
    *,
    dimension: str,
    start: datetime,
    end: datetime,
    limit: int,
) -> list[dict]:
    """Top-N breakdown (by page / country / device) for the filter bar."""
    if dimension not in {"page", "country", "device"}:
        raise ValueError("dimension must be one of: page, country, device")

    # dimension is validated against an allow-list above, so it's safe to
    # interpolate directly into the column position of the query.
    query = text(
        f"""
        SELECT
            {dimension} AS label,
            SUM(event_count) AS event_count,
            SUM(revenue) AS revenue
        FROM hourly_event_stats
        WHERE bucket BETWEEN :start AND :end
        GROUP BY {dimension}
        ORDER BY event_count DESC
        LIMIT :limit
        """
    )
    result = await db.execute(query, {"start": start, "end": end, "limit": limit})
    return [dict(r) for r in result.mappings().all()]


async def refresh_materialized_view_loop() -> None:
    """
    Background task started on app startup: periodically refreshes the
    materialized view so trend/top queries pick up recent events without
    ever recomputing the whole aggregation from the raw table on request.
    """
    while True:
        await asyncio.sleep(settings.materialized_view_refresh_seconds)
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    text("REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_event_stats")
                )
                await db.commit()
        except Exception:
            logger.exception("Failed to refresh hourly_event_stats")
