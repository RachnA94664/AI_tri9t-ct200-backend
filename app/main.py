from fastapi import FastAPI
from app.api import browse, selections
from app.db.base import Base, engine
from app.models import document, selection  # ensure models are registered with Base
from app.api import browse, selections, generation, retrieval

from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="CT-200 Document API")

Base.metadata.create_all(bind=engine)  # creates any missing tables on startup

app.include_router(browse.router)
app.include_router(selections.router)
app.include_router(generation.router)
app.include_router(retrieval.router)

@app.get("/")
def root():
    return {"status": "ok"}