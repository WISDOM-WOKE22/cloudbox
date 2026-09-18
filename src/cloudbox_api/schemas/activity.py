import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityEvent(BaseModel):
    event_id: str
    action: str
    actor_id: str
    resource_type: str
    resource_id: str
    resource_name: str
    occurred_at: str


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: uuid.UUID
    resource_name: str
    created_at: datetime
