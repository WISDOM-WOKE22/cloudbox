from collections.abc import AsyncGenerator

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cloudbox_api.core.config import settings
from cloudbox_api.db.base import Base
from cloudbox_api.dependencies.database import get_db
from cloudbox_api.main import create_app
from cloudbox_api.models import *  # noqa: F401, F403 — register models


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    session = session_factory()

    try:
        yield session
    finally:
        await session.close()
        # Clean all data after test
        async with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
        await engine.dispose()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[httpx.AsyncClient]:
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def registered_user(client: httpx.AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
    )
    return response.json()


@pytest.fixture
async def auth_tokens(client: httpx.AsyncClient, registered_user: dict) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "securepass123"},
    )
    return response.json()


@pytest.fixture
async def auth_header(auth_tokens: dict) -> dict:
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}
