from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_asset_service
from app.schemas.asset import (Cable, CableCreate, Computer, ComputerCreate,
                               Consumable, ConsumableCreate, NetworkDevice,
                               NetworkDeviceCreate, Peripheral,
                               PeripheralCreate, Phone, PhoneCreate, Printer,
                               PrinterCreate, Rack, RackCreate, SimCardItem,
                               SimCardItemCreate)
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/bulk", tags=["assets:bulk"])


@router.post(
    "/",
    response_model=List[
        Union[
            Computer,
            Printer,
            NetworkDevice,
            Phone,
            Peripheral,
            Consumable,
            Rack,
            Cable,
            SimCardItem,
        ]
    ],
    status_code=status.HTTP_201_CREATED,
)
def bulk_create_assets(
    assets_in: List[
        Union[
            ComputerCreate,
            PrinterCreate,
            NetworkDeviceCreate,
            PhoneCreate,
            PeripheralCreate,
            ConsumableCreate,
            RackCreate,
            CableCreate,
            SimCardItemCreate,
        ]
    ],
    service: AssetService = Depends(get_asset_service),
):
    """Bulk create multiple assets."""
    try:
        return service.bulk_create_assets(assets_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
