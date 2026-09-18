import json

import aio_pika

from cloudbox_api.core.config import settings

connection: aio_pika.abc.AbstractRobustConnection | None = None
channel: aio_pika.abc.AbstractChannel | None = None

EXCHANGE_NAME = "cloudbox.events"
ACTIVITY_QUEUE = "cloudbox.activity"
ACTIVITY_ROUTING_KEY = "activity"


async def init_rabbitmq() -> None:
    global connection, channel
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

        queue = await channel.declare_queue(ACTIVITY_QUEUE, durable=True)
        await queue.bind(exchange, routing_key=f"{ACTIVITY_ROUTING_KEY}.#")
    except Exception:
        connection = None
        channel = None


async def close_rabbitmq() -> None:
    global connection, channel
    if connection is not None:
        await connection.close()
    connection = None
    channel = None


async def publish_event(routing_key: str, event: dict) -> None:
    if channel is None:
        return

    try:
        exchange = await channel.get_exchange(EXCHANGE_NAME)
        message = aio_pika.Message(
            body=json.dumps(event, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=routing_key)
    except Exception:
        pass
