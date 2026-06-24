# refresh oauth tokens
import requests
import os
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from routers.models import OuraCodes, DailyMetric

# get variables from ENV
OURA_CLIENT_ID = os.getenv("OURA_CLIENT_ID")
OURA_CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET")
OURA_REDIRECT_URI = os.getenv("OURA_REDIRECT_URI")

token_url = "https://api.ouraring.com/oauth/token"

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
    
# pagination handler for endpoints
def fetch_all_pages(endpoint, db, params):
    return_list = []

    response = call_api(endpoint, db, params)
    data = response.json()

    return_list.extend(data["data"])

    # handle next_tokens
    while True:
        # get token for pagination
        next_token = data["next_token"]
        if next_token is None:
            break
        params["next_token"] = next_token

        new_response = call_api(endpoint, db, params)
        data = new_response.json()
        return_list.extend(data["data"])
    
    return return_list

# normalize raw daily_score payload (sleep, readiness, activity) from oura
def normalize_daily_score_data(payload, metric_type):
    # payload is a list of dicts [{}, {}, ...]
    if payload is None:
        return []

    allowed = {"sleep_score", "activity_score", "readiness_score"}

    if metric_type not in allowed:
        raise Exception("Wrong metric type")

    normalized_data = []

    skipped = 0

    for obj in payload:
        if obj.get("day") is None or obj.get("score") is None:
            skipped += 1
            continue

        new_obj = {
            "metric_date": obj.get("day"),
            metric_type: obj.get("score"),
        }

        normalized_data.append(new_obj)

    return {
    "records": normalized_data,
    "skipped": skipped
    }

# ingest normalized data into db
def ingest_data(data, metric_type, db):
    # data is a list of dicts [{}, {}, ...]
    if data is None:
        raise Exception("Payload is empty")
    
    allowed = {"sleep_score", "activity_score", "readiness_score"}

    if metric_type not in allowed:
        raise Exception("Wrong metric type")
    
    processed = 0

    # 1. Build the base insert
    for obj in data:
        statement = insert(DailyMetric).values(metric_date=obj.get("metric_date"), sleep_score=obj.get("sleep_score"), readiness_score=obj.get("readiness_score"), activity_score=obj.get("activity_score"))
        
        mapping = {
            "sleep_score": statement.excluded.sleep_score,
            "readiness_score": statement.excluded.readiness_score,
            "activity_score": statement.excluded.activity_score,
        }

        # define the conflict resolution
        upsert_stmt = statement.on_conflict_do_update(
            index_elements=['metric_date'],  # unique key column
            set_={
                metric_type: mapping.get(metric_type),
            }
        )

        db.execute(upsert_stmt)
        processed += 1
    db.commit()

    return processed