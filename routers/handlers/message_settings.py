import re

from aiogram import types, Router, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select

from routers.database.database import get_session
from routers.database.models import User
from routers.admin.role import AdminRoleFilter
from routers.keyboards.keyboard import admin_message_menu_def, cancel_keyboard

router = Router()

class GetSimpleMessage(StatesGroup):
    message = State()

class GetInlineMessage(StatesGroup):
    text = State()
    inline_text = State()
    inline_link = State()

class GetAnimeIdForSendMessage(StatesGroup):
    unique_id = State()

@router.message(F.text == "💬 Habar yuborish sozlamalari",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_message_settings(message: types.Message):
    await message.answer(text="💬 Habar yuborish sozlamalaridasiz: ", reply_markup=await admin_message_menu_def())

@router.message(F.text == "💬 Habar yuborish oddiy",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_message_simple(message: types.Message, state: FSMContext):
    await state.set_state(GetSimpleMessage.message)
    await message.answer(text="Yuborish uchun oddiy matn yuboring: ", reply_markup=await cancel_keyboard())

@router.message(GetSimpleMessage.message, F.text)
async def send_message_simple_process(message: types.Message, bot: Bot, state: FSMContext):
    text = message.text
    async with get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        count = 0
        for user in users:
            try:
                await bot.send_message(chat_id=user.telegram_id, text=text, parse_mode="MarkdownV2")
                count += 1
            except TelegramBadRequest:
                pass  # xatoni logga yozish mumkin
            except TelegramForbiddenError:
                pass
        await state.clear()
        await message.answer(text=f"Muvaffaqiyatli yuborildi:{count}", reply_markup=await admin_message_menu_def())

@router.message(F.text == "⚙️ Habar yuborish inline",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_message_inline(message: types.Message, state: FSMContext):
    await state.set_state(GetInlineMessage.text)
    await message.answer(text="Habar matnini yuboring", reply_markup=await cancel_keyboard())

@router.message(GetInlineMessage.text, F.text)
async def send_message_inline_process_text(message: types.Message, state: FSMContext):
    text = message.text
    await state.set_state(GetInlineMessage.inline_text)
    await state.update_data(text=text)
    await message.answer(text="Inline habar uchun matn yuboring: ", reply_markup=await cancel_keyboard())

@router.message(GetInlineMessage.inline_text, F.text)
async def send_message_inline_process_inline_text(message: types.Message, state: FSMContext):
    user_data = await state.update_data()
    text = user_data.get("text")
    inline_text = message.text
    if len(text) > 256:
        await message.answer("Matn 256 belgidan oshmasligi kerak!", reply_markup=await cancel_keyboard())
        return
    else:
        await state.set_state(GetInlineMessage.inline_link)
        await state.update_data(inline_text=inline_text)
        await message.answer(text="Iltimos endi inline linkini kirting: ")

@router.message(GetInlineMessage.inline_link, F.text)
async def send_message_inline_process_inline_link(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    text = user_data.get("text")
    inline_text = user_data.get("inline_text") or "inline text"
    inline_link = message.text.strip()
    link_pattern = r"https?://[^\s]+"  # Bu, http yoki https bilan boshlovchi barcha linklarni tutadi

    # Searching for the link in the message text
    match = re.search(link_pattern, inline_link)

    if match:
        # If a link is found, extract it
        link = match.group(0)
        async with get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=inline_text, url=link)]])
            count = 0
            for user in users:
                try:
                    await bot.send_message(text=text, reply_markup=inline_kb, chat_id=user.telegram_id)
                    count += 1
                except TelegramBadRequest:
                    pass
                except TelegramForbiddenError:
                    pass
        await state.clear()
        await message.answer(text=f"Muvaffqaiyatli yubrildi:{count} ", reply_markup=await admin_message_menu_def())

    else:
        await message.answer(f"Matnda link topilmadi.", reply_markup=await cancel_keyboard())


# @router.message(F.text == "🍥 Anime habar yuborish",
#                 F.chat.type == "private",
#                 AdminRoleFilter())
# async def send_anime_message(message: types.Message, state: FSMContext):
