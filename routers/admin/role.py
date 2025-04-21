
from routers.database.database import get_session
from aiogram import types
from aiogram.filters import BaseFilter
from routers.database.models import get_employee_by_chat_id

class AdminRoleFilter(BaseFilter):
    def __init__(self, *args, **kwargs):
        pass

    async def __call__(self, message: types.Message) -> bool:
        async with get_session() as session:
            is_admin = await get_employee_by_chat_id(chat_id=message.chat.id, session=session)
            return is_admin