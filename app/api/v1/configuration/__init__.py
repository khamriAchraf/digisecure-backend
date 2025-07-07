from fastapi import APIRouter

from app.api.v1.configuration.location import router as location_router

# from app.api.v1.configuration.manufacturer import router as manufacturer_router

router = APIRouter(prefix="/configuration")
router.include_router(location_router)
# router.include_router(manufacturer_router)
