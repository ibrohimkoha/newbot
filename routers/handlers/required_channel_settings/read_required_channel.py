from aiogram import types, Router, F
from sqlalchemy import select
from routers.admin.role import AdminRoleFilter
from routers.database.database import get_session
from routers.database.models import RequiredChannel
from routers.keyboards.keyboard import admin_settings_required_channel_def

router = Router()

@router.message(F.text == "📋 Kanallar ro‘yxati",
                F.chat.type == "private",
                AdminRoleFilter())
async def read_required_channel(message: types.Message):
    async with get_session() as session:
        channels = await session.execute(select(RequiredChannel))
        channels = channels.scalars().all()
        if not channels:
            await message.answer("Kanallar topilmadi", reply_markup=await admin_settings_required_channel_def())
            return
        msg = ""
        for channel in channels:
            msg += f"KanalID: {channel.channel_id}, username: {channel.username}, nomi: {channel.name}\n"
        await message.answer(text=msg, reply_markup=await admin_settings_required_channel_def())