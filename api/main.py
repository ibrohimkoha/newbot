from typing import List
import bcrypt
from django.db.models.fields import return_None

from api.dependencies.JWT.handlers import JWTHandler
from api.dependencies.JWT.bearer import JWTBearer
from api.functions.admin import has_admin, get_admin_data
from hash_functions import check_password
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.admin import LoginAdminSchema, AdminResponseSchema
from api.types.anime import AnimeType, AnimeStatus
from api.schemas.anime import AnimeCreationSchema
from api.db_commands.anime import anime_creation_cmd
from routers.database.database import get_session_for_api
from routers.database.models import Admin

router = APIRouter(prefix="/api", tags=["api"])

@router.get(path="/get-anime-add-types/", response_model=List[str], tags=["Anime"])
async def get_anime_add_types():
    return [anime_type.value for anime_type in AnimeType]

@router.get(path="/get-anime-add-status/", response_model=List[str], tags=["AnimeStatus"])
async def get_anime_add_status():
    return [anime_status.value for anime_status in AnimeStatus]

@router.post(path="/create-anime")
async def create_anime(data: AnimeCreationSchema, session: AsyncSession = Depends(get_session_for_api)):
    result = await anime_creation_cmd(data=data, session=session)
    return result

@router.post(path="/login-for-admin")
async def login_for_admin(data: LoginAdminSchema, session: AsyncSession = Depends(get_session_for_api)):
    admin = await session.execute(select(Admin).where(Admin.telegram_id == data.telegram_id))
    admin = admin.scalar()
    if not admin:
        raise HTTPException(detail="Admin topilmadi", status_code=status.HTTP_400_BAD_REQUEST)
    if check_password(data.password, admin.password):
        token = JWTHandler().create_token(telegram_id=admin.telegram_id, user_id=admin.id)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(detail="Kodni xato kiritdingiz", status_code=status.HTTP_400_BAD_REQUEST)


@router.get(path="/check-token/")
async def check_token(token: str = Depends(JWTBearer()), session: AsyncSession = Depends(get_session_for_api)):
    result = await has_admin(session=session, token=token)
    return result

@router.get(path="/get-admin-data/", response_model=AdminResponseSchema)
async def admin_data(token: str = Depends(JWTBearer()), session: AsyncSession = Depends(get_session_for_api)):
    admin = await get_admin_data(token=token, session=session)
    return admin

@router.post("/logout")
async def logout(token: str = Depends(JWTBearer())):
    return {"message": "Logged out successfully"}