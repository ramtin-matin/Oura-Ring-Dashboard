from routers.database import Base, engine

from fastapi import FastAPI

from routers import auth, metric, oura

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Oura Dashboard Info")
app.include_router(auth.router)
app.include_router(metric.router)
app.include_router(oura.router)