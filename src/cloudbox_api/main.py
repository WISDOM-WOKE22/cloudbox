from contextlib import asynccontextmanager

from fastapi import FastAPI

from cloudbox_api.api.router import router as api_router
from cloudbox_api.core.config import settings
from cloudbox_api.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    from cloudbox_api.core.queue import close_rabbitmq, init_rabbitmq
    from cloudbox_api.core.redis import close_redis, init_redis

    try:
        from cloudbox_api.core.storage import ensure_bucket_exists
        ensure_bucket_exists()
    except Exception:
        pass  # MinIO may not be available in tests or early development

    await init_redis()
    await init_rabbitmq()

    yield

    await close_rabbitmq()
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.include_router(api_router)

    return app


app = create_app()
