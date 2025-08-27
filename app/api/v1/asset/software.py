from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_asset_service
from app.api.v1.asset.utils import get_query_filters
from app.schemas.asset import (ComputerList, NetworkDeviceList, Software,
                               SoftwareCreate, SoftwareList, SoftwareUpdate,
                               SoftwareVersion, SoftwareVersionCreate,
                               SoftwareVersionList, SoftwareVersionUpdate,
                               VirtualMachineList)
from app.schemas.document_store import Document
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.asset_service import AssetService, PermissionError

router = APIRouter(prefix="/software", tags=["assets:software"])


@router.get("/", response_model=PaginatedResponse[SoftwareList])
def list_software(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=99999),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    service: AssetService = Depends(get_asset_service),
    filters: dict = Depends(get_query_filters),
):
    """List all software with optional filtering."""
    try:
        software_list, total = service.get_paginated_software(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )
        return create_paginated_response(
            data=software_list, total=total, page=page, per_page=per_page
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/", response_model=Software, status_code=status.HTTP_201_CREATED)
def create_software(
    software_in: SoftwareCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new software."""
    try:
        return service.create_software(software_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{software_id}", response_model=Software)
def get_software(
    software_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Get a specific software by ID."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        return software
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{software_id}/versions", response_model=list[SoftwareVersionList])
def get_software_with_versions(
    software_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Return only the versions array for a given software."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        return list(software.versions or [])
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{software_id}", response_model=Software)
def update_software(
    software_id: int,
    software_in: SoftwareUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a software."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        return service.update_software(software, software_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{software_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software(
    software_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a software."""
    try:
        software = service.get_software(software_id)
        if not software:
            raise HTTPException(status_code=404, detail="Software not found")
        service.delete_software(software)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Software Version endpoints
@router.post(
    "/versions", response_model=SoftwareVersion, status_code=status.HTTP_201_CREATED
)
def create_software_version(
    version_in: SoftwareVersionCreate,
    service: AssetService = Depends(get_asset_service),
):
    """Create a new software version."""
    try:
        return service.create_software_version(version_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software_version(
    version_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Delete a software version."""
    try:
        service.delete_software_version(version_id)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/versions/{version_id}", response_model=SoftwareVersion)
def update_software_version(
    version_id: int,
    version_in: SoftwareVersionUpdate,
    service: AssetService = Depends(get_asset_service),
):
    """Update a software version."""
    try:
        return service.update_software_version(version_id, version_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_software_version(
    version_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Soft delete a software version."""
    try:
        service.soft_delete_software_version(version_id)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/versions/{version_id}/computers/{computer_id}",
    response_model=ComputerList,
    status_code=status.HTTP_201_CREATED,
)
def attach_version_to_computer(
    version_id: int,
    computer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Attach a software version to a computer (installed)."""
    try:
        return service.attach_software_version_to_computer(version_id, computer_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/versions/{version_id}/computers/{computer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def detach_version_from_computer(
    version_id: int,
    computer_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Detach a software version from a computer (uninstalled)."""
    try:
        service.detach_software_version_from_computer(version_id, computer_id)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/versions/{version_id}/computers",
    response_model=list[ComputerList],
)
def list_computers_for_version(
    version_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """List computers that have the given software version, filtered by access and update permission."""
    try:
        return service.list_computers_for_software_version(version_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/versions/{version_id}/virtual-machines/{virtual_machine_id}",
    response_model=VirtualMachineList,
    status_code=status.HTTP_201_CREATED,
)
def attach_version_to_virtual_machine(
    version_id: int,
    virtual_machine_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Attach a software version to a virtual machine (installed)."""
    try:
        return service.attach_software_version_to_virtual_machine(
            version_id, virtual_machine_id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/versions/{version_id}/virtual-machines/{virtual_machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def detach_version_from_virtual_machine(
    version_id: int,
    virtual_machine_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Detach a software version from a virtual machine (uninstalled)."""
    try:
        service.detach_software_version_from_virtual_machine(
            version_id, virtual_machine_id
        )
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/versions/{version_id}/virtual-machines",
    response_model=list[VirtualMachineList],
)
def list_virtual_machines_for_version(
    version_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """List virtual machines that have the given software version, filtered by access and update permission."""
    try:
        return service.list_virtual_machines_for_software_version(version_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/versions/{version_id}/network-devices/{network_device_id}",
    response_model=NetworkDeviceList,
    status_code=status.HTTP_201_CREATED,
)
def attach_version_to_network_device(
    version_id: int,
    network_device_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Attach a software version to a network device (installed)."""
    try:
        return service.attach_software_version_to_network_device(
            version_id, network_device_id
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/versions/{version_id}/network-devices/{network_device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def detach_version_from_network_device(
    version_id: int,
    network_device_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Detach a software version from a network device (uninstalled)."""
    try:
        service.detach_software_version_from_network_device(
            version_id, network_device_id
        )
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/versions/{version_id}/network-devices",
    response_model=list[NetworkDeviceList],
)
def list_network_devices_for_version(
    version_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """List network devices that have the given software version, filtered by access and update permission."""
    try:
        return service.list_network_devices_for_software_version(version_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{software_id}/documents", response_model=list[Document])
def list_software_documents(
    software_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """List documents attached to a software."""
    try:
        return service.get_documents_for_software(software_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{software_id}/documents/{document_id}",
    response_model=Software,
    status_code=status.HTTP_201_CREATED,
)
def attach_document_to_software(
    software_id: int,
    document_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Attach a document to a software."""
    try:
        return service.attach_document_to_software(software_id, document_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/{software_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def detach_document_from_software(
    software_id: int,
    document_id: int,
    service: AssetService = Depends(get_asset_service),
):
    """Detach a document from a software."""
    try:
        service.detach_document_from_software(software_id, document_id)
        return None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
