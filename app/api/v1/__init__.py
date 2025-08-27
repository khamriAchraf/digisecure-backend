from fastapi import APIRouter

from app.api.v1.asset import router as asset_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.document_store import router as document_router

router = APIRouter()
router.include_router(asset_router)
router.include_router(compliance_router)
router.include_router(document_router)
