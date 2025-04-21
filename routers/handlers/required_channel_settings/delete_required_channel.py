from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from routers.database.database import get_session
from routers.database.models import RequiredChannel
from routers.admin.role import AdminRoleFilter
from routers.keyboards.keyboard import cancel_keyboard, admin_settings_required_channel_def

router = Router()

class DeleteChannelForm(StatesGroup):
    channel_id = State()

@router.message(F.text == "🗑 Kanalni o‘chirish",
                F.chat.type == "private",
                AdminRoleFilter())
async def delete_required_channel(message: types.Message, state: FSMContext):
    await state.set_state(DeleteChannelForm.channel_id)
    await message.answer("Iltimos kanalni idsi ni kiriting: ", reply_markup=await cancel_keyboard())

@router.message(DeleteChannelForm.channel_id, F.text)
async def delete_required_channel_process(message: types.Message, state: FSMContext):
    channel_id_text = message.text.strip()

    # ID raqam ekanligini tekshiramiz
    try:
        channel_id = int(channel_id_text)
    except ValueError:
        await message.answer("❌ Noto‘g‘ri ID format! Iltimos, faqat raqam kiriting.", reply_markup=await cancel_keyboard())
        return

    async with get_session() as session:
        result = await session.execute(
            select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
        )
        channel = result.scalar()

        if not channel:
            await message.answer("❌ Kanal topilmadi.", reply_markup=await cancel_keyboard())
            return

        await session.delete(channel)
        await session.commit()
        await message.answer("✅ Kanal muvaffaqiyatli olib tashlandi!", reply_markup=await admin_settings_required_channel_def())
        await state.clear()