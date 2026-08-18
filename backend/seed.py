"""
Standalone seeding script -- useful if you want to reset/repopulate data
without restarting the whole API.

Usage:
    python seed.py                # 30 days, ~3000 events/day (default)
    python seed.py --days 7 --events-per-day 1000
"""
import argparse
import asyncio

from sqlalchemy import text

from app.database import Base, engine
from app.services.fake_data import seed_historical


async def main(days: int, events_per_day: int) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inserted = await seed_historical(days=days, base_events_per_day=events_per_day)
    print(f"Inserted {inserted} events across the last {days} days.")

    async with engine.begin() as conn:
        await conn.execute(text("REFRESH MATERIALIZED VIEW hourly_event_stats"))
    print("Refreshed hourly_event_stats materialized view.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--events-per-day", type=int, default=3000)
    args = parser.parse_args()
    asyncio.run(main(args.days, args.events_per_day))
