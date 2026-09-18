import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.core.queue import publish_event
from cloudbox_api.models.activity import Activity
from cloudbox_api.schemas.activity import ActivityEvent


async def publish_activity_event(
    action: str,
    actor_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
    resource_name: str,
) -> None:
    event = ActivityEvent(
        event_id=str(uuid.uuid4()),
        action=action,
        actor_id=str(actor_id),
        resource_type=resource_type,
        resource_id=str(resource_id),
        resource_name=resource_name,
        occurred_at=datetime.now(timezone.utc).isoformat(),
    )
    await publish_event(f"activity.{action}", event.model_dump())


async def list_activities(db: AsyncSession, actor_id: uuid.UUID) -> list[Activity]:
    result = await db.execute(
        select(Activity)
        .where(Activity.actor_id == actor_id)
        .order_by(Activity.created_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())
