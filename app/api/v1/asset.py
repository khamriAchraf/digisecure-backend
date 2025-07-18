from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import get_asset_service
from app.schemas.asset import (AssetCreate, AssetUnion, AssetUpdate, Cable,
                               CableCreate, CableUpdate, Computer,
                               ComputerCreate, ComputerUpdate, Consumable,
                               ConsumableCreate, ConsumableUpdate,
                               NetworkDevice, NetworkDeviceCreate,
                               NetworkDeviceUpdate, Peripheral,
                               PeripheralCreate, PeripheralUpdate, Phone,
                               PhoneCreate, PhoneUpdate, Printer,
                               PrinterCreate, PrinterUpdate, Rack, RackCreate,
                               RackUpdate, SimCardItem, SimCardItemCreate,
                               SimCardItemUpdate)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/assets", tags=["assets"])

# Asset type mapping for validation
ASSET_TYPES = [
    "computer",
    "printer",
    "network_device",
    "phone",
    "peripheral",
    "consumable",
    "rack",
    "cable",
    "sim_card_item",
]


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in [
            "page",
            "per_page",
            "sort_by",
            "sort_order",
            "search",
            "asset_type",
            "warranty_expired",
        ]:
            filters[key] = value
    if "asset_type" in request.query_params:
        filters["type"] = request.query_params["asset_type"]
    if "warranty_expired" in request.query_params:
        filters["warranty_expired"] = (
            request.query_params["warranty_expired"].lower() == "true"
        )
    return filters


# Generic asset endpoints
@router.get("/{asset_id}", response_model=AssetUnion)
def get_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a single asset by ID. Returns the appropriate subtype."""
    try:
        asset = service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/", response_model=PaginatedResponse[AssetUnion])
def list_assets(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=99999, description="Number of items per page"),
    sort_by: Optional[str] = Query(None, description="Sort by column name"),
    sort_order: str = Query("asc", enum=["asc", "desc"], description="Sort order"),
    search: Optional[str] = Query(None, description="Search term"),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List assets with comprehensive filtering and pagination."""
    try:
        if "type" in filters and filters["type"] not in ASSET_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid asset type. Must be one of: {ASSET_TYPES}",
            )

        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=AssetUnion, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: Union[
        AssetCreate,
        ComputerCreate,
        PrinterCreate,
        NetworkDeviceCreate,
        PhoneCreate,
        PeripheralCreate,
        ConsumableCreate,
        RackCreate,
        CableCreate,
        SimCardItemCreate,
    ],
    service: AssetService = Depends(get_asset_service),
):
    """Create a new asset. The asset type is determined by the input schema."""
    try:
        return service.create_asset(asset_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{asset_id}", response_model=AssetUnion)
def update_asset(
    asset_id: int,
    asset_in: Union[
        AssetUpdate,
        ComputerUpdate,
        PrinterUpdate,
        NetworkDeviceUpdate,
        PhoneUpdate,
        PeripheralUpdate,
        ConsumableUpdate,
        RackUpdate,
        CableUpdate,
        SimCardItemUpdate,
    ],
    service: AssetService = Depends(get_asset_service),
):
    """Update an asset. Supports both base and subtype-specific fields."""
    try:
        asset = service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return service.update_asset(asset, asset_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete an asset."""
    try:
        asset = service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        service.delete_asset(asset)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Type-specific endpoints are simplified to use the main paginated endpoint
# with the `asset_type` filter. Example for computers:
@router.get("/computers/", response_model=PaginatedResponse[Computer])
def list_computers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all computers with optional filtering."""
    try:
        filters["type"] = "computer"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/computers/", response_model=Computer, status_code=status.HTTP_201_CREATED
)
def create_computer(
    computer_in: ComputerCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new computer."""
    try:
        return service.create_asset(computer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/computers/{computer_id}", response_model=Computer)
def get_computer(
    computer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific computer by ID."""
    try:
        computer = service.get_asset_by_type(computer_id, "computer")
        if not computer:
            raise HTTPException(status_code=404, detail="Computer not found")
        return computer
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/computers/{computer_id}", response_model=Computer)
def update_computer(
    computer_id: int,
    computer_in: ComputerUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a computer."""
    try:
        computer = service.get_asset_by_type(computer_id, "computer")
        if not computer:
            raise HTTPException(status_code=404, detail="Computer not found")
        return service.update_asset(computer, computer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Printer endpoints
@router.get("/printers/", response_model=PaginatedResponse[Printer])
def list_printers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all printers with optional filtering."""
    try:
        filters["type"] = "printer"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/printers/", response_model=Printer, status_code=status.HTTP_201_CREATED)
def create_printer(
    printer_in: PrinterCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new printer."""
    try:
        return service.create_asset(printer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/printers/{printer_id}", response_model=Printer)
def get_printer(
    printer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific printer by ID."""
    try:
        printer = service.get_asset_by_type(printer_id, "printer")
        if not printer:
            raise HTTPException(status_code=404, detail="Printer not found")
        return printer
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/printers/{printer_id}", response_model=Printer)
def update_printer(
    printer_id: int,
    printer_in: PrinterUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a printer."""
    try:
        printer = service.get_asset_by_type(printer_id, "printer")
        if not printer:
            raise HTTPException(status_code=404, detail="Printer not found")
        return service.update_asset(printer, printer_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Network Device endpoints
@router.get("/networkdevices/", response_model=PaginatedResponse[NetworkDevice])
def list_network_devices(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all network devices with optional filtering."""
    try:
        filters["type"] = "network_device"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/networkdevices/",
    response_model=NetworkDevice,
    status_code=status.HTTP_201_CREATED,
)
def create_network_device(
    network_device_in: NetworkDeviceCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new network device."""
    try:
        return service.create_asset(network_device_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/networkdevices/{network_device_id}", response_model=NetworkDevice)
def get_network_device(
    network_device_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific network device by ID."""
    try:
        network_device = service.get_asset_by_type(network_device_id, "network_device")
        if not network_device:
            raise HTTPException(status_code=404, detail="Network device not found")
        return network_device
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/networkdevices/{network_device_id}", response_model=NetworkDevice)
def update_network_device(
    network_device_id: int,
    network_device_in: NetworkDeviceUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a network device."""
    try:
        network_device = service.get_asset_by_type(network_device_id, "network_device")
        if not network_device:
            raise HTTPException(status_code=404, detail="Network device not found")
        return service.update_asset(network_device, network_device_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Phone endpoints
@router.get("/phones/", response_model=PaginatedResponse[Phone])
def list_phones(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all phones with optional filtering."""
    try:
        filters["type"] = "phone"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/phones/", response_model=Phone, status_code=status.HTTP_201_CREATED)
def create_phone(
    phone_in: PhoneCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new phone."""
    try:
        return service.create_asset(phone_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/phones/{phone_id}", response_model=Phone)
def get_phone(
    phone_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific phone by ID."""
    try:
        phone = service.get_asset_by_type(phone_id, "phone")
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        return phone
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/phones/{phone_id}", response_model=Phone)
def update_phone(
    phone_id: int,
    phone_in: PhoneUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a phone."""
    try:
        phone = service.get_asset_by_type(phone_id, "phone")
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        return service.update_asset(phone, phone_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Peripheral endpoints
@router.get("/peripherals/", response_model=PaginatedResponse[Peripheral])
def list_peripherals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all peripherals with optional filtering."""
    try:
        filters["type"] = "peripheral"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/peripherals/", response_model=Peripheral, status_code=status.HTTP_201_CREATED
)
def create_peripheral(
    peripheral_in: PeripheralCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new peripheral."""
    try:
        return service.create_asset(peripheral_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/peripherals/{peripheral_id}", response_model=Peripheral)
def get_peripheral(
    peripheral_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific peripheral by ID."""
    try:
        peripheral = service.get_asset_by_type(peripheral_id, "peripheral")
        if not peripheral:
            raise HTTPException(status_code=404, detail="Peripheral not found")
        return peripheral
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/peripherals/{peripheral_id}", response_model=Peripheral)
def update_peripheral(
    peripheral_id: int,
    peripheral_in: PeripheralUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a peripheral."""
    try:
        peripheral = service.get_asset_by_type(peripheral_id, "peripheral")
        if not peripheral:
            raise HTTPException(status_code=404, detail="Peripheral not found")
        return service.update_asset(peripheral, peripheral_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Consumable endpoints
@router.get("/consumables/", response_model=PaginatedResponse[Consumable])
def list_consumables(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all consumables with optional filtering."""
    try:
        filters["type"] = "consumable"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/consumables/", response_model=Consumable, status_code=status.HTTP_201_CREATED
)
def create_consumable(
    consumable_in: ConsumableCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new consumable."""
    try:
        return service.create_asset(consumable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/consumables/{consumable_id}", response_model=Consumable)
def get_consumable(
    consumable_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific consumable by ID."""
    try:
        consumable = service.get_asset_by_type(consumable_id, "consumable")
        if not consumable:
            raise HTTPException(status_code=404, detail="Consumable not found")
        return consumable
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/consumables/{consumable_id}", response_model=Consumable)
def update_consumable(
    consumable_id: int,
    consumable_in: ConsumableUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a consumable."""
    try:
        consumable = service.get_asset_by_type(consumable_id, "consumable")
        if not consumable:
            raise HTTPException(status_code=404, detail="Consumable not found")
        return service.update_asset(consumable, consumable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Rack endpoints
@router.get("/racks/", response_model=PaginatedResponse[Rack])
def list_racks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all racks with optional filtering."""
    try:
        filters["type"] = "rack"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/racks/", response_model=Rack, status_code=status.HTTP_201_CREATED)
def create_rack(
    rack_in: RackCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new rack."""
    try:
        return service.create_asset(rack_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/racks/{rack_id}", response_model=Rack)
def get_rack(
    rack_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific rack by ID."""
    try:
        rack = service.get_asset_by_type(rack_id, "rack")
        if not rack:
            raise HTTPException(status_code=404, detail="Rack not found")
        return rack
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/racks/{rack_id}", response_model=Rack)
def update_rack(
    rack_id: int,
    rack_in: RackUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a rack."""
    try:
        rack = service.get_asset_by_type(rack_id, "rack")
        if not rack:
            raise HTTPException(status_code=404, detail="Rack not found")
        return service.update_asset(rack, rack_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Cable endpoints
@router.get("/cables/", response_model=PaginatedResponse[Cable])
def list_cables(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all cables with optional filtering."""
    try:
        filters["type"] = "cable"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/cables/", response_model=Cable, status_code=status.HTTP_201_CREATED)
def create_cable(
    cable_in: CableCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new cable."""
    try:
        return service.create_asset(cable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/cables/{cable_id}", response_model=Cable)
def get_cable(
    cable_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific cable by ID."""
    try:
        cable = service.get_asset_by_type(cable_id, "cable")
        if not cable:
            raise HTTPException(status_code=404, detail="Cable not found")
        return cable
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/cables/{cable_id}", response_model=Cable)
def update_cable(
    cable_id: int,
    cable_in: CableUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a cable."""
    try:
        cable = service.get_asset_by_type(cable_id, "cable")
        if not cable:
            raise HTTPException(status_code=404, detail="Cable not found")
        return service.update_asset(cable, cable_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# SimCardItem endpoints
@router.get("/simcarditems/", response_model=PaginatedResponse[SimCardItem])
def list_sim_card_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all SIM card items with optional filtering."""
    try:
        filters["type"] = "sim_card_item"
        assets, total = service.get_paginated_assets(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=assets, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/simcarditems/", response_model=SimCardItem, status_code=status.HTTP_201_CREATED
)
def create_sim_card_item(
    sim_card_item_in: SimCardItemCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new SIM card item."""
    try:
        return service.create_asset(sim_card_item_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/simcarditems/{sim_card_item_id}", response_model=SimCardItem)
def get_sim_card_item(
    sim_card_item_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific SIM card item by ID."""
    try:
        sim_card_item = service.get_asset_by_type(sim_card_item_id, "sim_card_item")
        if not sim_card_item:
            raise HTTPException(status_code=404, detail="SIM card item not found")
        return sim_card_item
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/simcarditems/{sim_card_item_id}", response_model=SimCardItem)
def update_sim_card_item(
    sim_card_item_id: int,
    sim_card_item_in: SimCardItemUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a SIM card item."""
    try:
        sim_card_item = service.get_asset_by_type(sim_card_item_id, "sim_card_item")
        if not sim_card_item:
            raise HTTPException(status_code=404, detail="SIM card item not found")
        return service.update_asset(sim_card_item, sim_card_item_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Analytics endpoints
@router.get("/analytics/counts/by-type")
def get_asset_counts_by_type(
    service: AssetService = Depends(get_asset_service),
):
    """Get count of assets grouped by type."""
    try:
        return service.get_asset_count_by_type()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/analytics/counts/by-status")
def get_asset_counts_by_status(
    service: AssetService = Depends(get_asset_service),
):
    """Get count of assets grouped by status."""
    try:
        return service.get_asset_count_by_status()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/analytics/counts/by-location")
def get_asset_counts_by_location(
    service: AssetService = Depends(get_asset_service),
):
    """Get count of assets grouped by location."""
    try:
        return service.get_asset_count_by_location()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Bulk operations
@router.post(
    "/bulk/", response_model=List[AssetUnion], status_code=status.HTTP_201_CREATED
)
def bulk_create_assets(
    assets_in: List[
        Union[
            AssetCreate,
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
