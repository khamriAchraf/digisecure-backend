from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentBase(BaseModel):
    name: str
    description: Optional[str] = None
    folder_id: Optional[int] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    folder_id: Optional[int] = None


class Document(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionBase(BaseModel):
    version_number: int
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    uploaded_by: Optional[int] = None


class DocumentVersionCreate(BaseModel):
    # Version number will be computed server-side; file info provided after upload handling
    file_name: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None


class DocumentVersion(DocumentVersionBase):
    id: int
    document_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentWithVersions(Document):
    versions: List[DocumentVersion] = []


class DocumentFolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class DocumentFolderCreate(DocumentFolderBase):
    pass


class DocumentFolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class DocumentFolder(DocumentFolderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentFolderNode(BaseModel):
    id: int
    name: str
    children: List["DocumentFolderNode"] = []


class FolderContents(BaseModel):
    folder: DocumentFolder
    subfolders: List[DocumentFolder]
    documents: List[Document]


DocumentFolderNode.model_rebuild()
