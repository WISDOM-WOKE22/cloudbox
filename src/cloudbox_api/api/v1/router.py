from fastapi import APIRouter

from cloudbox_api.api.v1.routes import auth, files, folders, health, shares, users

router = APIRouter()

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(folders.router)
router.include_router(files.router)
router.include_router(shares.router)
