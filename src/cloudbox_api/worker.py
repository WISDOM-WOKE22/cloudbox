import asyncio
import json
import uuid

import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from cloudbox_api.core.config import settings
from cloudbox_api.core.queue import ACTIVITY_QUEUE
from cloudbox_api.models.activity import Activity

engine = create_async_engine(settings.DATABASE_URL, echo=False)
session_factory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def process_activity_event(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            event = json.loads(message.body.decode())
            async with session_factory() as session:
                activity = Activity(
                    id=uuid.UUID(event["event_id"]),
                    actor_id=uuid.UUID(event["actor_id"]),
                    action=event["action"],
                    resource_type=event["resource_type"],
                    resource_id=uuid.UUID(event["resource_id"]),
                    resource_name=event["resource_name"],
                )
                session.add(activity)
                await session.commit()
                print(f"[worker] Processed: {event['action']} on {event['resource_name']}")
        except Exception as e:
            print(f"[worker] Error processing message: {e}")


async def main() -> None:
    print("[worker] Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(ACTIVITY_QUEUE, durable=True)
        print(f"[worker] Listening on queue: {ACTIVITY_QUEUE}")

        await queue.consume(process_activity_event)

        # Keep the worker running
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
