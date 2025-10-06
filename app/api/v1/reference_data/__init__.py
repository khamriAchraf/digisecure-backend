from fastapi import APIRouter

from app.api.v1.reference_data.location import router as location_router
from app.api.v1.reference_data.manufacturer import \
    router as manufacturer_router
from app.api.v1.reference_data.operating_system import \
    router as operating_system_router

router = APIRouter(prefix="/reference_data")
router.include_router(location_router)
router.include_router(manufacturer_router)
router.include_router(operating_system_router)
