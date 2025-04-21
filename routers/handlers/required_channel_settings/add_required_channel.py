from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select

from routers.admin.role import AdminRoleFilter
from routers.database.database import get_session
from routers.keyboards.keyboard import cancel_keyboard, admin_settings_required_channel_def
from routers.database.models import RequiredChannel
router = Router()

class RequiredchannelAdd(StatesGroup):
    channel_id = State()
    username = State()
    name = State()


@router.message(F.text == "📢 Kanal qo‘shish",
                F.chat.type == "private",
                AdminRoleFilter())
async def add_required_channel(message: types.Message, state: FSMContext):
    await state.set_state(RequiredchannelAdd.channel_id)
    await message.answer("Iltimos kanal id sini kiriting: \n Kanalga botni admin qiling: \n Minussiz kiriting idni: bo'lmasa xato beradi:  ", reply_markup=await cancel_keyboard())

@router.message(RequiredchannelAdd.channel_id, F.text)
async def process_channel_id(message: types.Message, state: FSMContext, bot:Bot):
    try:
        chan_id = int(message.text.strip())
        if chan_id > 0:
            chan_id = -chan_id
    except ValueError:
        await message.answer("Iltimos raqamlar bilan kiriting", reply_markup=await cancel_keyboard())
        return

    try:
        chat = await bot.get_chat(chan_id)
        if not chat.type in ("channel", "supergroup"):
            await message.answer("Bu ID kanalga tegishli emas.", reply_markup=await cancel_keyboard())
            return
        async with get_session() as session:
            exist_channel = await session.execute(select(RequiredChannel).where(RequiredChannel.channel_id == chan_id))
            exist_channel = exist_channel.scalar()
            if exist_channel:
                await message.answer("Kanal oldin qo'shilgan: ", reply_markup=await cancel_keyboard())
                return
        await state.update_data(chan_id=chan_id)
        await message.answer("kanal usernameni yokida kanal maxfiy linkini tashlang:", reply_markup=await cancel_keyboard())
        await state.set_state(RequiredchannelAdd.username)
    except TelegramAPIError:
        await message.answer("Kanal topilmadi yoki bot kanalga qo‘shilmagan.")
        return

@router.message(RequiredchannelAdd.username, F.text)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if len(username) > 99:
        await message.answer("Username xatosi", reply_markup=await cancel_keyboard())
        return
    await message.answer("Endi kanalingiz uchun saqlash nomini bering: ", reply_markup=await cancel_keyboard())
    await state.update_data(username=username)
    await state.set_state(RequiredchannelAdd.name)


@router.message(RequiredchannelAdd.name, F.text)
async def process_name_add(message: types.Message, state: FSMContext):
    name = message.text.strip()
    user_data = await state.get_data()
    username = user_data.get("username")
    chan_id = user_data.get("chan_id")
    async with get_session() as session:
        exist_channel = await session.execute(select(RequiredChannel).where(RequiredChannel.channel_id == chan_id))
        exist_channel = exist_channel.scalar()
        if exist_channel:
            await message.answer("Bu id lik kanal qo'shilgan: ", reply_markup=await admin_settings_required_channel_def())
            await state.clear()
            return
        if len(username) > 99:
            await message.answer("Username xatosi", reply_markup=await admin_settings_required_channel_def())
            await state.clear()
            return
        channel = RequiredChannel(channel_id=chan_id, username=username, name=name)
        session.add(channel)
        await session.commit()
        await message.answer("Kanal muvaffaqiyatli qo'shildi!", reply_markup=await admin_settings_required_channel_def())
        await state.clear()








