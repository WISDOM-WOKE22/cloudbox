from fastapi import APIRouter

from cloudbox_api.api.v1.router import router as v1_router
from cloudbox_api.core.config import settings

router = APIRouter()

router.include_router(v1_router, prefix=settings.API_V1_PREFIX)
