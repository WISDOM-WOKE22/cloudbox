from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from cloudbox_api.core.rate_limit import check_login_rate_limit
from cloudbox_api.dependencies.database import get_db
from cloudbox_api.schemas.auth import MessageResponse, RefreshRequest, TokenResponse
from cloudbox_api.schemas.user import UserCreate, UserResponse
from cloudbox_api.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await auth_service.register(db, user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    await check_login_rate_limit(request)
    return await auth_service.login(db, form_data.username, form_data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    return await auth_service.refresh(db, body.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await auth_service.logout(db, body.refresh_token)
    return MessageResponse(message="Successfully logged out")
