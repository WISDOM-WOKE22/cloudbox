import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from cloudbox_api.models.share import Permission


class ShareCreate(BaseModel):
    shared_with_id: uuid.UUID
    permission: Permission


class ShareUpdate(BaseModel):
    permission: Permission


class ShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource_type: str
    resource_id: uuid.UUID
    owner_id: uuid.UUID
    shared_with_id: uuid.UUID
    permission: str
    created_at: datetime
