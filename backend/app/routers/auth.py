import os
import requests 
from .database import get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from .models import OuraCodes
from sqlalchemy.orm import Session
from sqlalchemy import select
from urllib.parse import urlencode

router = APIRouter(
    prefix="/auth/oura",
    tags=["auth"],
)

# OAuth 2 section
# get variables from ENV
OURA_CLIENT_ID = os.getenv("OURA_CLIENT_ID")
OURA_CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET")
OURA_REDIRECT_URI = os.getenv("OURA_REDIRECT_URI")

token_url = "https://api.ouraring.com/oauth/token"

# login route to oura
@router.get("/login")
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
@router.get("/callback")
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