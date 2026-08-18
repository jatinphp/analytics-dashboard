import asyncio
import logging
import math
import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from app.database import AsyncSessionLocal
from app.models import Event
from app.config import settings
from app.websocket_manager import manager

logger = logging.getLogger("fake_data")
fake = Faker()

EVENT_TYPES = ["page_view", "click", "add_to_cart", "signup", "purchase"]
# Rough weights so page_view dominates and purchase is rare, like real traffic.
EVENT_WEIGHTS = [0.55, 0.25, 0.10, 0.06, 0.04]

PAGES = [
    "/", "/pricing", "/docs", "/blog", "/blog/launch-week",
    "/product/dashboard", "/product/api", "/signup", "/checkout", "/about",
]
COUNTRIES = ["US", "GB", "DE", "IN", "BR", "JP", "CA", "FR", "AU", "NG"]
DEVICES = ["desktop", "mobile", "tablet"]


def _random_event(created_at: datetime) -> dict:
    event_type = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]
    revenue = 0.0
    if event_type == "purchase":
        revenue = round(random.uniform(9.0, 299.0), 2)

    return {
        "event_type": event_type,
        "user_id": f"u_{random.randint(1, 4000)}",
        "page": random.choice(PAGES),
        "country": random.choice(COUNTRIES),
        "device": random.choices(DEVICES, weights=[0.5, 0.4, 0.1], k=1)[0],
        "revenue": revenue,
        "created_at": created_at,
    }


def _hour_of_day_weight(hour: int) -> float:
    """Simple sinusoidal traffic curve so seeded history has visible daily
    peaks/troughs instead of being flat noise -- makes the trend chart and
    moving average actually mean something."""
    return 0.4 + 0.6 * (0.5 + 0.5 * math.sin((hour - 8) / 24 * 2 * math.pi))


async def seed_historical(days: int = 30, base_events_per_day: int = 3000) -> int:
    """
    Bulk-inserts `days` worth of synthetic history, biased so daytime hours
    get more events than the middle of the night. Returns the row count
    inserted. Safe to call multiple times -- it always adds new rows rather
    than checking for existing ones, so run it once per fresh database.
    """
    now = datetime.now(timezone.utc)
    total_inserted = 0

    async with AsyncSessionLocal() as db:
        for day_offset in range(days, 0, -1):
            day_start = now - timedelta(days=day_offset)
            batch = []
            for hour in range(24):
                weight = _hour_of_day_weight(hour)
                n_events = int(base_events_per_day / 24 * weight * random.uniform(0.85, 1.15))
                for _ in range(n_events):
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    ts = day_start.replace(
                        hour=hour, minute=minute, second=second, microsecond=0
                    )
                    batch.append(_random_event(ts))
            db.add_all([Event(**row) for row in batch])
            await db.commit()
            total_inserted += len(batch)
            logger.info(
                "Seeded %s events for day -%s (%s remaining)",
                len(batch), day_offset, day_offset - 1,
            )

    return total_inserted


async def live_event_generator() -> None:
    """
    Background task: forever emits a new fake event every ~0.4-1.5s,
    persists it, and broadcasts it to every connected WebSocket client.
    This stands in for a real production event stream (page views,
    clicks, purchases) coming from application servers or a message
    queue like Kafka/Kinesis.
    """
    while True:
        await asyncio.sleep(
            random.uniform(settings.fake_event_min_interval, settings.fake_event_max_interval)
        )
        event = _random_event(datetime.now(timezone.utc))

        try:
            async with AsyncSessionLocal() as db:
                db.add(Event(**event))
                await db.commit()
        except Exception:
            logger.exception("Failed to persist live event")
            continue

        await manager.broadcast({"type": "event", "data": event})
