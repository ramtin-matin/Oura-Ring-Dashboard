import requests 

from app.database import Base, engine, get_db

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import DailyMetric, OuraCodes
from app.schemas import DailyMetricCreate, DailyMetricResponse, OuraCodeUpsert
from fastapi.responses import RedirectResponse

from urllib.parse import urlencode
from datetime import datetime, timezone
import requests

import os

from dotenv import load_dotenv
load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Oura Dashboard Info")

# base api function for oura endpoints
def call_api(endpoint, db, params):
    # get tokens from database
    statement = select(OuraCodes)
    row = db.scalars(statement).first()

    # users first time connecting to Oura
    if row is None:
        raise Exception("connect to Oura first!")
    
    # make response requests
    try:
        url = f"https://api.ouraring.com/v2/{endpoint}"
        headers = { 
        'Authorization': 'Bearer ' + row.access_token
        }
        response = requests.get(url, headers=headers, params=params, timeout=15) 
        
        # invalid / expired
        if response.status_code == 401:
            # token expired, try to refresh
            new_tokens = refresh_access_token(row.refresh_token)
            # store new tokens in db
            row.access_token = new_tokens["access_token"]
            row.refresh_token = new_tokens["refresh_token"]
            db.commit()
            db.refresh(row)

            # retry the request with the new token
            new_headers = { 
            'Authorization': 'Bearer ' + new_tokens["access_token"]
            }

            return requests.get(url, headers=new_headers, timeout=15)
        
        return response
    
    except Exception as e:
         raise Exception("API call failed: ", e)
    
# refresh oauth tokens
def refresh_access_token(refresh_token):
    try:
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": OURA_CLIENT_ID,
            "client_secret": OURA_CLIENT_SECRET
        }
        response = requests.post(token_url, data=token_data)

        if response.ok:
            return response.json()
        else:
            raise Exception("Response failed with error: ", response.status_code)

    except Exception as e:
        raise Exception("Refresh failed: ", e)


# Start of OAuth 2 section
# get variables from ENV
OURA_CLIENT_ID = os.getenv("OURA_CLIENT_ID")
OURA_CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET")
OURA_REDIRECT_URI = os.getenv("OURA_REDIRECT_URI")

token_url = "https://api.ouraring.com/oauth/token"

# login route to oura
@app.get("/auth/oura/login")
def oura_login():
    params = {
        "response_type": "code",
        "client_id": OURA_CLIENT_ID,
        "redirect_uri": OURA_REDIRECT_URI,
        "scope": "personal daily heartrate",
    }

    authorization_url = (
        "https://cloud.ouraring.com/oauth/authorize?"
        + urlencode(params)
    )

    return RedirectResponse(authorization_url)

# callback logic for oura
@app.get("/auth/oura/callback")
def oura_callback(code: str, db: Session = Depends(get_db)):
    response = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OURA_REDIRECT_URI,
            "client_id": OURA_CLIENT_ID,
            "client_secret": OURA_CLIENT_SECRET,
        },
        timeout=15,
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    data = response.json()

    statement = select(OuraCodes)
    row = db.scalars(statement).first() # get the existing token row, if it exists

    if row: # update tokens
        row.access_token = data["access_token"]
        row.refresh_token = data["refresh_token"]

        db.commit()
        db.refresh(row)
    else: # add tokens
        tokens = OuraCodes(
            access_token = data["access_token"],
            refresh_token = data["refresh_token"],
        )

        db.add(tokens)
        db.commit()
        db.refresh(tokens)
    
    return data

# End of OAuth 2 section

@app.get("/sleep")
def get_sleep_scores(db: Session = Depends(get_db)):
    params={ 
        'start_date': '2026-06-12', 
        'end_date': '2026-06-15',
    }

    response = call_api("usercollection/sleep", db, params)
    print(response.request.url)
    return response.json()
