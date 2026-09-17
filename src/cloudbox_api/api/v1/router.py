from fastapi import APIRouter

from cloudbox_api.api.v1.routes import auth, health, users

router = APIRouter()

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(users.router)
