from datetime import datetime

from pydantic import BaseModel


class LiveEvent(BaseModel):
    event_type: str
    user_id: str
    page: str
    country: str
    device: str
    revenue: float
    created_at: datetime


class SummaryMetrics(BaseModel):
    events_today: int
    active_users_5m: int
    revenue_today: float
    events_per_min_last_hour: float


class TrendPoint(BaseModel):
    bucket: datetime
    event_count: int
    unique_users: int
    revenue: float
    moving_avg_events: float


class TopItem(BaseModel):
    label: str
    event_count: int
    revenue: float
