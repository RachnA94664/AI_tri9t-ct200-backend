from fastapi import FastAPI
from app.api import browse, selections
from app.db.base import Base, engine
from app.models import document, selection  # ensure models are registered with Base

app = FastAPI(title="CT-200 Document API")

Base.metadata.create_all(bind=engine)  # creates any missing tables on startup

app.include_router(browse.router)
app.include_router(selections.router)


@app.get("/")
def root():
    return {"status": "ok"}