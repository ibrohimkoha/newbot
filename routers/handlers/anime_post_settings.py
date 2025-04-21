from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import F, types, Bot, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy import select

from routers.admin.role import AdminRoleFilter
from routers.database.database import get_session
from routers.database.models import Channel, Anime, Post
from routers.handlers.anime_language_settings import AddChannelStates, DeleteChannelStates
from routers.keyboards.keyboard import admin_post_menu_def, user_main_menu_def, cancel_keyboard, admin_main_menu_def
from config import ADMINS
from text_form import response_for_anime

router = Router()

# Admin Post Settings Menu Handler
@router.message(F.text == "📮 Post sozlamalari",
                F.chat.type == "private",
                AdminRoleFilter())
async def post_settings(message: types.Message):
    await message.answer("⚙️ Post sozlamalaridasiz", reply_markup=await admin_post_menu_def())

# Add Post Handlers
# 1) Kanal ID so‘rash
@router.message(F.text == "➕ Post yuborish uchun qo'shish",
                F.chat.type == "private",
                AdminRoleFilter())
async def cmd_add_channel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Iltimos, kanal ID (raqam) kiriting:",
        reply_markup=await cancel_keyboard()
    )
    await state.set_state(AddChannelStates.channel)

# 2) Kanal ID kelganda – DBda tekshirish yoki nom so‘rash
@router.message(AddChannelStates.channel, F.text)
async def process_channel_id(message: types.Message, state: FSMContext):
    text = message.text.strip()
    chan_id = int(text)
    async with get_session() as session:
        res = await session.execute(select(Channel).where(Channel.channel_id == chan_id))
        channel = res.scalar_one_or_none()

    if channel:
        await message.answer(
            "✅ Bu kanal bazada mavjud!",
            reply_markup=await admin_post_menu_def()
        )
        await state.clear()
    else:
        await state.update_data(temp_channel_id=chan_id)
        await message.answer(
            "Iltimos, kanal nomini kiriting:",
            reply_markup=await cancel_keyboard()
        )
        await state.set_state(AddChannelStates.channel_name)

# 3) Kanal nomi kelganda – DBga yozish
@router.message(AddChannelStates.channel_name)
async def process_channel_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    chan_id = data["temp_channel_id"]
    chan_name = message.text.strip()

    async with get_session() as session:
        new_channel = Channel(channel_id=chan_id, name=chan_name)
        session.add(new_channel)
        await session.commit()

    await message.answer(
        f"✅ Kanal qo'shildi:\n"
        f"• DB ID: {new_channel.id}\n"
        f"• Telegram ID: {new_channel.channel_id}\n"
        f"• Nom: {new_channel.name}",
        reply_markup=await admin_post_menu_def()
    )
    await state.clear()

# View Channels Handler
@router.message(F.text == "👁 Post uchun kanallarni ko'rish",
                F.chat.type == "private",
                AdminRoleFilter())
async def view_channels(message: types.Message, bot: Bot):
    async with get_session() as session:
        result = await session.execute(select(Channel))
        channels = result.scalars().all()

    if not channels:
        await message.answer("Hech qanday kanal mavjud emas.", reply_markup=await admin_post_menu_def())
        return

    lines = ["Kanallar ro'yxati:\n"]
    for ch in channels:
        try:
            chat = await bot.get_chat(ch.channel_id)
            username = chat.username or "none"
        except Exception:
            username = "none"

        lines.append(
            f"ID: {ch.id}, Channel ID: {ch.channel_id}, Name: {ch.name}, Username: @{username}"
        )

    text = "\n".join(lines)
    await message.answer(text, reply_markup=await admin_post_menu_def())

# Delete Channel Handlers
@router.message(F.text == "🗑 Post uchun kanalni o'chirish",
                F.chat.type == "private",
                AdminRoleFilter())
async def cmd_delete_channel(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, o'chirmoqchi bo'lgan kanal ID kiriting:", reply_markup=await cancel_keyboard())
    await state.set_state(DeleteChannelStates.channel)

@router.message(DeleteChannelStates.channel, F.text)
async def process_delete_channel(message: types.Message, state: FSMContext):
    ch_id = int(message.text.strip())
    async with get_session() as session:
        channel = (await session.execute(select(Channel).where(Channel.id == ch_id))).scalar()
        if not channel:
            await message.answer("Kanal topilmadi!", reply_markup=await admin_post_menu_def())
            await state.clear()
            return
        await session.delete(channel)
        await session.commit()
        await message.answer("✅ Kanal o'chirildi!", reply_markup=await admin_post_menu_def())
    await state.clear()

class WaitingForPost(StatesGroup):
    anime_code     = State()   # 1‑bosqich: kod so‘rash
    choose_channel = State()   # 2‑bosqich: kanal tanlash

# 1) “📝 Post tayyorlash” tugmasi bosilganda:
@router.message(F.text == "📝 Post tayyorlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def cmd_prepare_post(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Iltimos, post qilmoqchi bo‘lgan anime kodini (unique_id) kiriting:",
        reply_markup=await cancel_keyboard()
    )
    await state.set_state(WaitingForPost.anime_code)

# 2) Anime kodini qabul qilib, bazadan olish va kanallarni ko‘rsatish
@router.message(WaitingForPost.anime_code, F.text)
async def process_anime_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    if not code.isdigit():
        return await message.answer(
            "Iltimos, to‘g‘ri raqam kiriting:",
            reply_markup=await cancel_keyboard()
        )

    async with get_session() as session:
        result = await session.execute(select(Anime).where(Anime.unique_id == int(code)))
        anime = result.scalar_one_or_none()

    if not anime:
        return await message.answer(
            "Bunday kodli anime topilmadi. Qayta kiriting:",
            reply_markup=await cancel_keyboard()
        )

    await state.update_data(anime_id=anime.id)

    # Kanallarni olish
    async with get_session() as session:
        ch_res = await session.execute(select(Channel))
        channels = ch_res.scalars().all()

    if not channels:
        await message.answer(
            "Hozircha kanal ro‘yxati bo‘sh!",
            reply_markup=await admin_post_menu_def()
        )
        return await state.clear()

    # Inline keyboard bilan ko‘rsatamiz
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ch.name or str(ch.channel_id),
                    callback_data=f"post_to_channel_{ch.id}_{anime.id}"
                )
            ]
            for ch in channels
        ]
    )
    await message.answer(
        f"Anime: <b>{anime.title}</b>\nKanallardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.clear()

# 3) Kanal tanlanganda postni yuborish
@router.callback_query(F.data.startswith("post_to_channel_"))
async def process_channel_choice(callback: CallbackQuery, bot: Bot):
    _, _, _, channel_db_id, anime_id = callback.data.split("_")
    anime_id = int(anime_id)
    channel_db_id = int(channel_db_id)
    async with get_session() as session:
        anime   = (await session.execute(select(Anime).where(Anime.id == anime_id))).scalar_one_or_none()
        channel = (await session.execute(select(Channel).where(Channel.id == channel_db_id))).scalar_one_or_none()

    if not anime or not channel:
        await callback.message.answer("Xatolik: anime yoki kanal topilmadi.")
        await callback.answer()
        return
    try:
        chat = await bot.get_chat(channel.channel_id)
    except TelegramForbiddenError:
        await callback.message.delete()
        await callback.message.answer(
            text="⛔️ Bot kanalga qo‘shilmagan yoki admin emas.",
            reply_markup=await admin_post_menu_def()
        )
        await callback.answer()
        return
    except TelegramBadRequest:
        await callback.message.delete()
        await callback.message.answer(
            text="❌ Kanal topilmadi. Kanal o‘chirilgan yoki ID noto‘g‘ri.",
            reply_markup=await admin_post_menu_def()
        )
        await callback.answer()
        return

    # Postni yuboramiz
    caption = await response_for_anime(anime=anime)
    bot_info = await bot.get_me()
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Ko'rish 🔹", url=f"https://t.me/{bot_info.username}?start={anime.unique_id}")]
    ])
    try:
        msg = await bot.send_photo(
            chat_id=channel.channel_id,
            photo=anime.image,
            caption=caption,
            parse_mode="HTML",
            reply_markup=inline_kb
        )
    except TelegramForbiddenError:
        await callback.message.delete()
        await callback.message.answer("⛔️ Bot kanalga rasm yubora olmaydi. Iltimos, ruxsatlarni tekshiring.")
        await callback.answer()
        return

    # DB ga saqlaymiz
    async with get_session() as session:
        post = Post(channel_id=channel.id, anime_id=anime.id, message_id=msg.message_id)
        session.add(post)
        await session.commit()

    await callback.message.delete()
    await callback.message.answer("✅ Post muvaffaqiyatli yuborildi va saqlandi.", reply_markup=await admin_main_menu_def())
    await callback.answer()

@router.message(F.text == "👤 Admin panelga qaytish",
                F.chat.type == "private",
                AdminRoleFilter())
async def statistics(message: types.Message):
    await message.answer("Admin panelga qaytishingiz uchun iltimos tugmalardan foydalaning",
                             reply_markup=await admin_main_menu_def())
