from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import aggregator

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)):
    return await aggregator.get_summary(db)


@router.get("/trends")
async def trends(
    start: datetime | None = Query(None, description="Defaults to 7 days ago"),
    end: datetime | None = Query(None, description="Defaults to now"),
    event_type: str | None = Query(None),
    country: str | None = Query(None),
    device: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    end = end or datetime.now(timezone.utc)
    start = start or end - timedelta(days=7)
    return await aggregator.get_trends(
        db,
        start=start,
        end=end,
        event_type=event_type,
        country=country,
        device=device,
    )


@router.get("/top")
async def top(
    dimension: Literal["page", "country", "device"] = Query("page"),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    end = end or datetime.now(timezone.utc)
    start = start or end - timedelta(days=7)
    return await aggregator.get_top(db, dimension=dimension, start=start, end=end, limit=limit)
