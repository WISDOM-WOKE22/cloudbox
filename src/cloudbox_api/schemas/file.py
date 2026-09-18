import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=127)
    size: int = Field(ge=0, default=0)
    folder_id: uuid.UUID | None = None


class FileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class FileMove(BaseModel):
    folder_id: uuid.UUID | None = None


class UploadUrlResponse(BaseModel):
    upload_url: str
    expires_in: int


class DownloadUrlResponse(BaseModel):
    download_url: str
    expires_in: int


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    folder_id: uuid.UUID | None
    mime_type: str
    size: int
    storage_key: str | None
    created_at: datetime
    updated_at: datetime
