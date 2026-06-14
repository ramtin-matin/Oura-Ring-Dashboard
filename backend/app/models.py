from datetime import date

from sqlalchemy import Date, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class DailyMetric(Base):
  __tablename__ = "daily_metrics"

  id: Mapped[int] = mapped_column(primary_key=True)
  metric_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
  sleep_score: Mapped[int] = mapped_column(Integer, nullable=True)
  readiness_score: Mapped[int] = mapped_column(Integer, nullable=True)
  activity_score: Mapped[int] = mapped_column(Integer, nullable=True)
