from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, user
from app.core.config import settings
from app.core.logger import logger

app = FastAPI()

logger.info(f"Starting API with parameters: {settings}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")


@app.get("/health")
def read_root():
    return {"message": "API is alive"}
