from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import auth


app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")

@app.get("/health")
def read_root():
    return {"message": "API is alive"}


