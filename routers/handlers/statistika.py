from aiogram import Router, types, F
from sqlalchemy import select, func

from routers.database.database import get_session
from routers.database.models import User
from routers.admin.role import AdminRoleFilter

router = Router()


@router.message(F.text == "📊 Statistika",
                F.chat.type == "private",
                AdminRoleFilter())
async def get_statics(message: types.Message):
    async with get_session() as session:
        result = await session.execute(select(func.count(User.id)))
        users_count = result.scalar()

        await message.answer(f"👥 Foydalanuvchilar soni: {users_count}")

