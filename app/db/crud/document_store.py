from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session, joinedload

from app.db.models.document_store import (Document, DocumentFolder,
                                          DocumentVersion)


# Documents CRUD
def get_document(db: Session, document_id: int) -> Optional[Document]:
    return (
        db.query(Document)
        .options(joinedload(Document.versions))
        .filter(Document.id == document_id)
        .first()
    )


def list_documents(db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
    return (
        db.query(Document)
        .options(joinedload(Document.versions))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_paginated_documents(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Document], int]:
    query: Query = db.query(Document)

    # Filters
    if filters:
        for key, value in filters.items():
            if hasattr(Document, key):
                if value is None:
                    query = query.filter(getattr(Document, key).is_(None))
                elif value != "":
                    query = query.filter(getattr(Document, key) == value)

    # Search in name/description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Document.name.ilike(search_term),
                Document.description.ilike(search_term),
            )
        )

    total = query.count()

    # Sorting
    if sort_by and hasattr(Document, sort_by):
        column = getattr(Document, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    else:
        query = query.order_by(Document.id.asc())

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    items = query.all()
    return items, total


def get_cursor_documents(
    db: Session,
    cursor: Optional[int] = None,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    search: Optional[str] = None,
    filters: Optional[dict] = None,
) -> Tuple[List[Document], int]:
    query: Query = db.query(Document)

    # Filters
    if filters:
        for key, value in filters.items():
            if hasattr(Document, key):
                if value is None:
                    query = query.filter(getattr(Document, key).is_(None))
                elif value != "":
                    query = query.filter(getattr(Document, key) == value)

    # Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Document.name.ilike(search_term),
                Document.description.ilike(search_term),
            )
        )

    # Cursor
    if cursor is not None:
        if sort_order.lower() == "desc":
            query = query.filter(Document.id < cursor)
        else:
            query = query.filter(Document.id > cursor)

    total = query.count()

    # Sorting fallback
    if sort_by and hasattr(Document, sort_by):
        column = getattr(Document, sort_by)
    else:
        column = Document.id

    if sort_order.lower() == "desc":
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())

    # Limit
    query = query.limit(per_page)
    items = query.all()
    return items, total


def create_document(
    db: Session,
    name: str,
    description: Optional[str] = None,
    folder_id: Optional[int] = None,
) -> Document:
    document = Document(name=name, description=description, folder_id=folder_id)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_document(
    db: Session,
    document: Document,
    name: Optional[str] = None,
    description: Optional[str] = None,
    folder_id: Optional[int] = None,
) -> Document:
    if name is not None:
        document.name = name
    if description is not None:
        document.description = description
    if folder_id is not None:
        document.folder_id = folder_id
    db.commit()
    db.refresh(document)
    return document


# Folders CRUD
def get_folder(db: Session, folder_id: int) -> Optional[DocumentFolder]:
    return db.query(DocumentFolder).filter(DocumentFolder.id == folder_id).first()


def list_folders(db: Session, parent_id: Optional[int] = None) -> List[DocumentFolder]:
    query = db.query(DocumentFolder)
    if parent_id is None:
        query = query.filter(DocumentFolder.parent_id.is_(None))
    else:
        query = query.filter(DocumentFolder.parent_id == parent_id)
    return query.order_by(DocumentFolder.name.asc()).all()


def create_folder(db: Session, name: str, parent_id: Optional[int]) -> DocumentFolder:
    folder = DocumentFolder(name=name, parent_id=parent_id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def update_folder(
    db: Session,
    folder: DocumentFolder,
    name: Optional[str] = None,
    parent_id: Optional[int] = None,
) -> DocumentFolder:
    if name is not None:
        folder.name = name
    if parent_id is not None:
        folder.parent_id = parent_id
    db.commit()
    db.refresh(folder)
    return folder


def delete_folder(db: Session, folder: DocumentFolder) -> None:
    db.delete(folder)
    db.commit()


def delete_document(db: Session, document: Document) -> None:
    db.delete(document)
    db.commit()


# Versions CRUD
def get_document_version(db: Session, version_id: int) -> Optional[DocumentVersion]:
    return db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()


def list_document_versions(db: Session, document_id: int) -> List[DocumentVersion]:
    return (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.asc())
        .all()
    )


def get_next_version_number(db: Session, document_id: int) -> int:
    max_version: Optional[int] = (
        db.query(func.max(DocumentVersion.version_number))
        .filter(DocumentVersion.document_id == document_id)
        .scalar()
    )
    return (max_version or 0) + 1


def create_document_version(
    db: Session,
    document_id: int,
    file_path: str,
    file_name: str,
    file_size: Optional[int] = None,
    checksum: Optional[str] = None,
    uploaded_by: Optional[int] = None,
) -> DocumentVersion:
    version_number = get_next_version_number(db, document_id)
    version = DocumentVersion(
        document_id=document_id,
        version_number=version_number,
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        checksum=checksum,
        uploaded_by=uploaded_by,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def delete_document_version(db: Session, version: DocumentVersion) -> None:
    db.delete(version)
    db.commit()
