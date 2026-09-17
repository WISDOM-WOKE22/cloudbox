from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.db.session import async_session


async def get_db() -> AsyncGenerator[AsyncSession]:
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
