from contextlib import asynccontextmanager

from fastapi import FastAPI

from cloudbox_api.api.router import router as api_router
from cloudbox_api.core.config import settings
from cloudbox_api.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
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
