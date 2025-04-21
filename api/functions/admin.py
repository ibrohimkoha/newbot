from fastapi import HTTPException, status
from sqlalchemy import select

from api.dependencies.JWT.handlers import JWTHandler
from routers.database.models import Admin


async def has_admin(session, token):
    data = JWTHandler().decode_jwt(token=token)
    admin = await session.execute(select(Admin).where(Admin.telegram_id == data["sub"]))
    admin = admin.scalar()
    if not admin:
        raise HTTPException(detail="This token not valid", status_code=status.HTTP_401_UNAUTHORIZED)
    return HTTPException(detail="Token Valid", status_code=status.HTTP_200_OK)

async def get_admin_data(session, token):
    data = JWTHandler().decode_jwt(token=token)
    admin = await session.execute(select(Admin).where(Admin.telegram_id == data["sub"]))
    admin = admin.scalar()
    if not admin:
        raise HTTPException(detail="This token not valid", status_code=status.HTTP_401_UNAUTHORIZED)
    return admin