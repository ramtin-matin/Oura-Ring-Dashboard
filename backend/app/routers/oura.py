from fastapi import APIRouter, Depends
from dependencies import fetch_all_pages
from .database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
  prefix="/oura",
  tags=["oura"]
)

@router.get("/daily_sleep")
def get_sleep_scores(db: Session = Depends(get_db)):
    params={ 
        'start_date': '2026-05-15', 
        'end_date': '2026-06-15',
        'fields': 'day,score',
    }

    return_list = fetch_all_pages("usercollection/daily_sleep", db, params)    
    return return_list

@router.get("/daily_readiness")
def get_readiness_scores(db: Session = Depends(get_db)):
    params={ 
        'start_date': '2025-01-15', 
        'end_date': '2026-06-15',
        'fields': 'day,score',
    }

    return_list = fetch_all_pages("usercollection/daily_readiness", db, params)    
    return return_list

@router.get("/daily_activity")
def get_activity_scores(db: Session = Depends(get_db)):
    params={ 
        'start_date': '2025-01-15', 
        'end_date': '2026-06-15',
        'fields': 'day,score',
    }

    return_list = fetch_all_pages("usercollection/daily_activity", db, params)    
    return return_list