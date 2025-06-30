from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import auth, role, user
from app.core.config import settings
from app.core.logger import logger
from app.core.rate_limiting import limiter
from app.db.models.role import Permission
from app.db.session import SessionLocal

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

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
app.include_router(role.router, prefix="/api/v1")

permissions_cache = []


@app.on_event("startup")
def load_permissions_cache():
    global permissions_cache
    with SessionLocal() as db:
        permissions_cache = db.query(Permission).all()


@app.get("/health")
@limiter.limit("10/minute")
def read_root(request: Request):
    return {"message": "API is alive"}
