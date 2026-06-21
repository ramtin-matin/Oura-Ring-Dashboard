from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

class OuraCodeUpsert(BaseModel):
  access_token: str
  refresh_token: str

class DailyMetricCreate(BaseModel):
  metric_date: date
  sleep_score: int | None = None
  readiness_score: int | None = None
  activity_score: int | None = None

class DailyMetricResponse(DailyMetricCreate):
  model_config = ConfigDict(from_attributes=True)

  id: int