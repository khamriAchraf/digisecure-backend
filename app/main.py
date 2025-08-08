import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1 import auth, group, role, schema, table_config, user
from app.api.v1 import compliance as compliance_module
from app.api.v1.asset import router as asset_router
from app.api.v1.reference_data import router as reference_data_router
from app.core.config import settings
from app.core.logger import (clear_log_context, logger, set_request_id,
                             set_user_id)
from app.core.rate_limiting import limiter
from app.db.models.role import Permission
from app.db.session import SessionLocal
from app.services import auth_service

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
app.include_router(group.router, prefix="/api/v1")
app.include_router(asset_router, prefix="/api/v1")
app.include_router(compliance_module.router, prefix="/api/v1")
app.include_router(schema.router, prefix="/api/v1")
app.include_router(table_config.router, prefix="/api/v1")
app.include_router(reference_data_router, prefix="/api/v1")

permissions_cache = []


@app.on_event("startup")
def load_permissions_cache():
    global permissions_cache
    with SessionLocal() as db:
        permissions_cache = db.query(Permission).all()


@app.get("/health")
@limiter.limit("10/minute")
def read_root(request: Request):
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as e:
        return {"status": "error", "detail": f"Database connection failed: {str(e)}"}
    return {"status": "ok"}


@app.middleware("http")
async def logging_context_middleware(request: Request, call_next):
    # Set request_id from header or generate
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(req_id)
    # Try to extract user_id from Authorization header
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        user_id = auth_service.decode_access_token(token)
    set_user_id(str(user_id) if user_id else None)
    try:
        response = await call_next(request)
        return response
    finally:
        clear_log_context()
