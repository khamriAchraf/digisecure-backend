import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import has_permission
from app.db.crud import document_store as document_crud
from app.db.models.document_store import Document as DocumentModel
from app.db.models.document_store import DocumentFolder as DocumentFolderModel
from app.db.models.document_store import \
    DocumentVersion as DocumentVersionModel
from app.db.models.user import User
from app.schemas.document_store import DocumentFolder as DocumentFolderSchema
from app.schemas.document_store import (DocumentFolderNode, DocumentUpdate,
                                        FolderContents)


class PermissionError(Exception):
    pass


class DocumentStoreService:
    def __init__(
        self, db: Session, current_user: User, storage_root: str = "./data/documents"
    ):
        self.db = db
        self.current_user = current_user
        self.storage_root = storage_root

    # Documents
    def get_document(self, document_id: int) -> DocumentModel:
        logger.info(
            f"User {self.current_user.id} attempts to READ document {document_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "read", "document"):
            raise PermissionError("Not allowed to read documents.")
        doc = document_crud.get_document(self.db, document_id)
        return doc

    def get_paginated_documents(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[DocumentModel], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST documents at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "document"):
            raise PermissionError("Not allowed to list documents.")
        return document_crud.get_paginated_documents(
            self.db,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )

    def get_cursor_documents(
        self,
        cursor: Optional[int] = None,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> Tuple[List[DocumentModel], int]:
        logger.info(
            f"User {self.current_user.id} attempts to LIST documents with cursor at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "list", "document"):
            raise PermissionError("Not allowed to list documents.")
        return document_crud.get_cursor_documents(
            self.db,
            cursor=cursor,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
        )

    def create_document_with_version(
        self,
        name: str,
        description: Optional[str],
        file_name: str,
        file_bytes: bytes,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        folder_id: Optional[int] = None,
    ) -> DocumentModel:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE document '{name}' with initial version at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "document"):
            raise PermissionError("Not allowed to create documents.")

        # Create the document record first
        # Optional: validate folder_id exists
        if folder_id is not None:
            folder = document_crud.get_folder(self.db, folder_id)
            if folder is None:
                raise HTTPException(status_code=404, detail="Folder not found")

        document = document_crud.create_document(
            self.db, name=name, description=description, folder_id=folder_id
        )

        # Save initial version (v1)
        self._save_version(
            document_id=document.id,
            file_name=file_name,
            file_bytes=file_bytes,
            file_size=file_size,
            checksum=checksum,
        )

        # Reload with versions
        created = document_crud.get_document(self.db, document.id)
        return created if created else document

    def update_document(
        self, document: DocumentModel, doc_in: DocumentUpdate
    ) -> DocumentModel:
        logger.info(
            f"User {self.current_user.id} attempts to UPDATE document {document.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "document"):
            raise PermissionError("Not allowed to update documents.")
        return document_crud.update_document(
            self.db,
            document=document,
            name=doc_in.name,
            description=doc_in.description,
            folder_id=doc_in.folder_id,
        )

    def delete_document(self, document: DocumentModel) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE document {document.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "document"):
            raise PermissionError("Not allowed to delete documents.")
        # Delete all version files from disk
        versions = document_crud.list_document_versions(self.db, document.id)
        for v in versions:
            try:
                if v.file_path and os.path.exists(v.file_path):
                    os.remove(v.file_path)
            except OSError:
                logger.warning(f"Failed to delete file at {v.file_path}")
        document_crud.delete_document(self.db, document)

    # Versions / File handling
    def upload_new_version(
        self,
        document_id: int,
        file_name: str,
        file_bytes: bytes,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
    ) -> DocumentVersionModel:
        logger.info(
            f"User {self.current_user.id} attempts to UPLOAD document version for {document_id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "update", "document"):
            raise PermissionError("Not allowed to upload document versions.")

        document = document_crud.get_document(self.db, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")

        return self._save_version(
            document_id=document_id,
            file_name=file_name,
            file_bytes=file_bytes,
            file_size=file_size,
            checksum=checksum,
        )

    def list_versions(self, document_id: int) -> List[DocumentVersionModel]:
        if not has_permission(self.current_user, "read", "document"):
            raise PermissionError("Not allowed to list document versions.")
        return document_crud.list_document_versions(self.db, document_id)

    def delete_version(self, version: DocumentVersionModel) -> None:
        logger.info(
            f"User {self.current_user.id} attempts to DELETE document version {version.id} at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "delete", "document"):
            raise PermissionError("Not allowed to delete document versions.")
        # remove file
        try:
            if version.file_path and os.path.exists(version.file_path):
                os.remove(version.file_path)
        except OSError:
            logger.warning(f"Failed to delete file at {version.file_path}")
        document_crud.delete_document_version(self.db, version)

    # Folders
    def list_folders(
        self, parent_id: Optional[int] = None
    ) -> List[DocumentFolderModel]:
        if not has_permission(self.current_user, "read", "document"):
            raise PermissionError("Not allowed to list folders.")
        return document_crud.list_folders(self.db, parent_id)

    def get_folder(self, folder_id: int) -> DocumentFolderModel:
        if not has_permission(self.current_user, "read", "document"):
            raise PermissionError("Not allowed to read folders.")
        folder = document_crud.get_folder(self.db, folder_id)
        return folder

    def create_folder(self, name: str, parent_id: Optional[int]) -> DocumentFolderModel:
        if not has_permission(self.current_user, "create", "document"):
            raise PermissionError("Not allowed to create folders.")
        if (
            parent_id is not None
            and document_crud.get_folder(self.db, parent_id) is None
        ):
            raise HTTPException(status_code=404, detail="Parent folder not found")
        return document_crud.create_folder(self.db, name, parent_id)

    def update_folder(
        self, folder: DocumentFolderModel, name: Optional[str], parent_id: Optional[int]
    ) -> DocumentFolderModel:
        if not has_permission(self.current_user, "update", "document"):
            raise PermissionError("Not allowed to update folders.")
        if (
            parent_id is not None
            and document_crud.get_folder(self.db, parent_id) is None
        ):
            raise HTTPException(status_code=404, detail="Parent folder not found")
        return document_crud.update_folder(self.db, folder, name, parent_id)

    def delete_folder(self, folder: DocumentFolderModel) -> None:
        if not has_permission(self.current_user, "delete", "document"):
            raise PermissionError("Not allowed to delete folders.")
        # Deleting a folder cascades to subfolders and documents (via FK on documents)
        document_crud.delete_folder(self.db, folder)

    # Folder contents and tree
    def get_folder_contents(self, folder_id: Optional[int] = None) -> FolderContents:
        if not has_permission(self.current_user, "read", "document"):
            raise PermissionError("Not allowed to read folders.")
        if folder_id is None:
            # null folder: return documents with folder_id NULL and no subfolders
            docs, _ = document_crud.get_paginated_documents(
                self.db, page=1, per_page=1000, filters={"folder_id": None}
            )
            # Represent the "null" container as a virtual folder node
            virtual = DocumentFolderSchema(
                id=0,
                name="Uncategorized",
                parent_id=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            return FolderContents(folder=virtual, subfolders=[], documents=docs)
        else:
            folder = document_crud.get_folder(self.db, folder_id)
            if folder is None:
                raise HTTPException(status_code=404, detail="Folder not found")
            subfolders = document_crud.list_folders(self.db, parent_id=folder_id)
            docs, _ = document_crud.get_paginated_documents(
                self.db, page=1, per_page=1000, filters={"folder_id": folder_id}
            )
            return FolderContents(
                folder=DocumentFolderSchema.model_validate(folder),
                subfolders=[DocumentFolderSchema.model_validate(f) for f in subfolders],
                documents=docs,
            )

    def get_folder_tree(self) -> DocumentFolderNode:
        if not has_permission(self.current_user, "read", "document"):
            raise PermissionError("Not allowed to read folders.")

        def build_node(folder: DocumentFolderModel) -> DocumentFolderNode:
            children = document_crud.list_folders(self.db, parent_id=folder.id)
            return DocumentFolderNode(
                id=folder.id,
                name=folder.name,
                children=[build_node(ch) for ch in children],
            )

        # virtual root with top-level folders as children
        top_level = document_crud.list_folders(self.db, parent_id=None)
        return DocumentFolderNode(
            id=0, name="root", children=[build_node(f) for f in top_level]
        )

    def _save_version(
        self,
        document_id: int,
        file_name: str,
        file_bytes: bytes,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
    ) -> DocumentVersionModel:
        # Ensure storage directory
        doc_dir = os.path.join(self.storage_root, str(document_id))
        os.makedirs(doc_dir, exist_ok=True)

        # Write to a temporary path first
        temp_path = os.path.join(doc_dir, file_name)
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        # Create DB entry to get version number
        version = document_crud.create_document_version(
            self.db,
            document_id=document_id,
            file_path=temp_path,
            file_name=file_name,
            file_size=file_size,
            checksum=checksum,
            uploaded_by=self.current_user.id,
        )

        # Rename to include version number
        base, ext = os.path.splitext(file_name)
        versioned_name = f"{base}_v{version.version_number}{ext}"
        final_path = os.path.join(doc_dir, versioned_name)
        try:
            os.replace(temp_path, final_path)
        except OSError:
            logger.warning(
                "Could not rename uploaded file to versioned name; keeping original"
            )
            final_path = temp_path

        if final_path != version.file_path:
            version.file_path = final_path
            self.db.commit()
            self.db.refresh(version)

        return version
