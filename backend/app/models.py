from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Event(Base):
    """
    A single analytics event. This is the append-only fact table that
    everything else (materialized view, trend queries, live feed) derives
    from -- deliberately simple so the interesting work happens in SQL.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    user_id: Mapped[str] = mapped_column(String(50), index=True)
    page: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(2))
    device: Mapped[str] = mapped_column(String(20))
    revenue: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
