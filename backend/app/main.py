import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.routers import metrics, ws
from app.services import aggregator, fake_data
from app.websocket_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

INIT_SQL_PATH = Path(__file__).parent / "db" / "init.sql"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create the raw `events` table if it doesn't exist yet.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for statement in INIT_SQL_PATH.read_text().split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))

    # 2. Seed historical fake data on first run only (empty table).
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM events"))
        count = result.scalar_one()
    if count == 0:
        logger.info("events table is empty -- seeding fake historical data...")
        inserted = await fake_data.seed_historical(days=30, base_events_per_day=3000)
        logger.info("Seeded %s historical events", inserted)
        async with engine.begin() as conn:
            await conn.execute(text("REFRESH MATERIALIZED VIEW hourly_event_stats"))

    # 3. Start background tasks: WebSocket manager (Redis or in-memory),
    #    the live fake event stream, and the materialized view refresh loop.
    await manager.startup()
    live_task = asyncio.create_task(fake_data.live_event_generator())
    refresh_task = asyncio.create_task(aggregator.refresh_materialized_view_loop())

    yield

    live_task.cancel()
    refresh_task.cancel()
    await manager.shutdown()


app = FastAPI(title="Real-time Analytics Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router)
app.include_router(ws.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
