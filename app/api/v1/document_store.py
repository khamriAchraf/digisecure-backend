from typing import List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     Request, UploadFile, status)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.crud import document_store as document_crud
from app.db.models.document_store import \
    DocumentVersion as DocumentVersionModel
from app.db.models.user import User
from app.schemas.document_store import (Document, DocumentFolder,
                                        DocumentFolderCreate,
                                        DocumentFolderNode,
                                        DocumentFolderUpdate, DocumentUpdate,
                                        DocumentVersion, DocumentWithVersions,
                                        FolderContents)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.document_store import DocumentStoreService, PermissionError

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DocumentStoreService:
    return DocumentStoreService(db, current_user)


def get_query_filters(request: Request) -> dict:
    filters = {}
    for key, value in request.query_params.items():
        if key not in [
            "page",
            "per_page",
            "sort_by",
            "sort_order",
            "search",
            "cursor",
        ]:
            filters[key] = value
    return filters


@router.get("/", response_model=PaginatedResponse[Document])
def list_documents(
    page: Optional[int] = Query(
        None, ge=1, description="Page number (mutually exclusive with cursor)"
    ),
    per_page: int = Query(20, ge=1, le=1000),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    search: Optional[str] = Query(None),
    cursor: Optional[int] = Query(
        None, description="Cursor for infinite scroll (mutually exclusive with page)"
    ),
    filters: dict = Depends(get_query_filters),
    service: DocumentStoreService = Depends(get_document_service),
):
    if page is not None and cursor is not None:
        raise HTTPException(
            status_code=400, detail="Provide either 'page' or 'cursor', not both."
        )
    try:
        if cursor is not None:
            items, total = service.get_cursor_documents(
                cursor=cursor,
                per_page=per_page,
                sort_by=sort_by,
                sort_order=sort_order,
                search=search,
                filters=filters,
            )
            page_number = 1
            return create_paginated_response(
                data=items, total=total, page=page_number, per_page=per_page
            )
        else:
            page_number = page or 1
            items, total = service.get_paginated_documents(
                page=page_number,
                per_page=per_page,
                sort_by=sort_by,
                sort_order=sort_order,
                search=search,
                filters=filters,
            )
            return create_paginated_response(
                data=items, total=total, page=page_number, per_page=per_page
            )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/", response_model=DocumentWithVersions, status_code=status.HTTP_201_CREATED
)
async def create_document(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    folder_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    service: DocumentStoreService = Depends(get_document_service),
):
    try:
        file_bytes = await file.read()
        created = service.create_document_with_version(
            name=name,
            description=description,
            file_name=file.filename,
            file_bytes=file_bytes,
            file_size=len(file_bytes),
            checksum=None,
            folder_id=folder_id,
        )
        return created
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Folders endpoints (declared before dynamic document routes to avoid conflicts)
@router.get("/folders", response_model=List[DocumentFolder])
def list_folders(
    parent_id: Optional[int] = Query(
        None, description="List folders within a parent folder; omit for root"
    ),
    service: DocumentStoreService = Depends(get_document_service),
):
    try:
        return service.list_folders(parent_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/folders", response_model=DocumentFolder, status_code=status.HTTP_201_CREATED
)
def create_folder(
    folder_in: DocumentFolderCreate,
    service: DocumentStoreService = Depends(get_document_service),
):
    try:
        return service.create_folder(folder_in.name, folder_in.parent_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/folders/{folder_id}", response_model=DocumentFolder)
def update_folder(
    folder_id: int,
    folder_in: DocumentFolderUpdate,
    service: DocumentStoreService = Depends(get_document_service),
):
    try:
        folder = service.get_folder(folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        return service.update_folder(folder, folder_in.name, folder_in.parent_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Get Folder Tree (complete hierarchy)
@router.get("/folders/tree", response_model=DocumentFolderNode)
def get_folder_tree(service: DocumentStoreService = Depends(get_document_service)):
    try:
        return service.get_folder_tree()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Get Folder Contents (details, subfolders, documents)
@router.get("/folders/{folder_id}", response_model=FolderContents)
def get_folder_contents(
    folder_id: str,
    service: DocumentStoreService = Depends(get_document_service),
):
    try:
        if folder_id.lower() in ("null", "none"):
            return service.get_folder_contents(None)
        try:
            fid = int(folder_id)
        except ValueError:
            raise HTTPException(
                status_code=422, detail="folder_id must be an integer or 'null'"
            )
        return service.get_folder_contents(fid)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int, service: DocumentStoreService = Depends(get_document_service)
):
    try:
        folder = service.get_folder(folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        service.delete_folder(folder)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{document_id}", response_model=DocumentWithVersions)
def get_document(
    document_id: int, service: DocumentStoreService = Depends(get_document_service)
):
    try:
        doc = service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.patch("/{document_id}", response_model=Document)
def update_document(
    document_id: int,
    doc_in: DocumentUpdate,
    service: DocumentStoreService = Depends(get_document_service),
):
    try:
        doc = service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return service.update_document(doc, doc_in)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int, service: DocumentStoreService = Depends(get_document_service)
):
    try:
        doc = service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        service.delete_document(doc)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{document_id}/versions", response_model=List[DocumentVersion])
def list_versions(
    document_id: int, service: DocumentStoreService = Depends(get_document_service)
):
    try:
        return service.list_versions(document_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/{document_id}/versions",
    response_model=DocumentVersion,
    status_code=status.HTTP_201_CREATED,
)
async def upload_version(
    document_id: int,
    file: UploadFile = File(...),
    service: DocumentStoreService = Depends(get_document_service),
):
    try:
        file_bytes = await file.read()
        version = service.upload_new_version(
            document_id=document_id,
            file_name=file.filename,
            file_bytes=file_bytes,
            file_size=len(file_bytes),
            checksum=None,
        )
        return version
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_version(
    version_id: int, service: DocumentStoreService = Depends(get_document_service)
):
    try:
        version: DocumentVersionModel | None = document_crud.get_document_version(
            service.db, version_id
        )
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        service.delete_version(version)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/versions/{version_id}/download")
def download_version(
    version_id: int, service: DocumentStoreService = Depends(get_document_service)
):
    try:
        version: DocumentVersionModel | None = document_crud.get_document_version(
            service.db, version_id
        )
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        # Enforce read permission via service
        service.list_versions(version.document_id)
        # Permission: read document
        # Reuse service method to enforce read permission via list/get
        # Validate file existence
        if not version.file_path:
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(
            path=version.file_path,
            filename=version.file_name,
            media_type="application/octet-stream",
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
