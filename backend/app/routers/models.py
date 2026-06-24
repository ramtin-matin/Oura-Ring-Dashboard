from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from routers.database import Base

class DailyMetric(Base):
  __tablename__ = "daily_metrics"

  id: Mapped[int] = mapped_column(primary_key=True)
  metric_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
  sleep_score: Mapped[int] = mapped_column(Integer, nullable=True)
  readiness_score: Mapped[int] = mapped_column(Integer, nullable=True)
  activity_score: Mapped[int] = mapped_column(Integer, nullable=True)

class OuraCodes(Base):
  __tablename__ = "oura_codes"

  id: Mapped[int] = mapped_column(primary_key=True)
  access_token: Mapped[str] = mapped_column(String, unique=True)
  refresh_token: Mapped[str] = mapped_column(String, unique=True)