from fastapi import APIRouter, Depends
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import DailyMetric
from .database import get_db
from dependencies import fetch_all_pages, normalize_daily_score_data, ingest_data

router = APIRouter(
    prefix="/metrics",
    tags=["metric"],
)


# get daily_metrics from db
@router.get("/db")
def get_all_rows_from_db(start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db)):
    statement = select(DailyMetric)

    if start_date is not None:
        statement = statement.where(DailyMetric.metric_date >= start_date)
    
    if end_date is not None:
        statement = statement.where(DailyMetric.metric_date <= end_date)
    
    statement = statement.order_by(DailyMetric.metric_date.desc())

    rows = db.scalars(statement).all()
    return rows

@router.post("/ingest/daily_sleep")
def ingest_daily_sleep_into_db(db: Session = Depends(get_db)):
    params={ 
        'start_date': '2025-01-15', 
        'end_date': '2026-06-15',
        'fields': 'day,score',
    }

    return_list = fetch_all_pages("usercollection/daily_sleep", db, params)
    normalized = normalize_daily_score_data(return_list, "sleep_score")
    processed_count = ingest_data(normalized["records"], "sleep_score", db)
    return {"processed_count" : processed_count, "skipped" : normalized["skipped"]}


@router.post("/ingest/daily_readiness")
def ingest_daily_readiness_into_db(db: Session = Depends(get_db)):
    params={ 
        'start_date': '2025-01-15', 
        'end_date': '2026-06-15',
        'fields': 'day,score',
    }

    return_list = fetch_all_pages("usercollection/daily_readiness", db, params)
    normalized = normalize_daily_score_data(return_list, "readiness_score")
    processed_count = ingest_data(normalized["records"], "readiness_score", db)
    return {"processed_count" : processed_count, "skipped" : normalized["skipped"]}


@router.post("/ingest/daily_activity")
def ingest_daily_activity_into_db(db: Session = Depends(get_db)):
    params={ 
        'start_date': '2025-01-15', 
        'end_date': '2026-06-15',
        'fields': 'day,score',
    }

    return_list = fetch_all_pages("usercollection/daily_activity", db, params)
    normalized = normalize_daily_score_data(return_list, "activity_score")
    processed_count = ingest_data(normalized["records"], "activity_score", db)
    return {"processed_count" : processed_count, "skipped" : normalized["skipped"]}