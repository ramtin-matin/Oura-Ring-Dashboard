from app.database import Base, engine, get_db

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import DailyMetric
from app.schemas import DailyMetricCreate, DailyMetricResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Oura Dashboard Info")

@app.post("/metrics", response_model=DailyMetricResponse)
def create_metric(
  metric_data: DailyMetricCreate,
  db: Session = Depends(get_db)
):
  metric = DailyMetric(
    metric_date = metric_data.metric_date,
    sleep_score = metric_data.sleep_score,
    readiness_score = metric_data.readiness_score,
    activity_score = metric_data.activity_score
  )

  db.add(metric)
  db.commit()
  db.refresh(metric)

  return metric

@app.get("/metrics", response_model=list[DailyMetricResponse])
def get_all_metrics(db: Session = Depends(get_db)):
  statement = select(DailyMetric).order_by(DailyMetric.metric_date.desc())

  return db.scalars(statement).all()

