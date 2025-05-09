import re
import asyncio
from aiogram import types, Router, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select

from routers.database.database import get_session
from routers.database.models import User, Anime, AnimeLanguage
from routers.admin.role import AdminRoleFilter
from routers.keyboards.keyboard import admin_message_menu_def, cancel_keyboard
from text_form import response_for_anime

router = Router()

class GetSimpleMessage(StatesGroup):
    message = State()

class GetInlineMessage(StatesGroup):
    text = State()
    inline_text = State()
    inline_link = State()

class GetAnimeIdForSendMessage(StatesGroup):
    unique_id = State()

class GetImageMessage(StatesGroup):
    photo = State()

class GetVideoMessage(StatesGroup):
    video = State()

class GetFileMessage(StatesGroup):
    file = State()

class GetForwardMessage(StatesGroup):
    forward = State()

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


@router.message(F.text == "🍥 Anime habar yuborish",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_anime_message(message: types.Message, state: FSMContext):
    await state.set_state(GetAnimeIdForSendMessage.unique_id)
    await message.answer(text="Iltimos anime kodini yuboring: ", reply_markup=await cancel_keyboard())


@router.message(GetAnimeIdForSendMessage.unique_id, F.text)
async def send_anime_message_process(message: types.Message, state: FSMContext, bot: Bot):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer("Anime topilmadi? ", reply_markup=await cancel_keyboard())
                return
            languages = await session.execute(select(AnimeLanguage).filter(AnimeLanguage.anime_id == anime.id))
            languages = languages.scalars().all()
            if not languages:
                await message.answer("Animeda til topilmadi! ", reply_markup=await cancel_keyboard())
                return

            inline_kb = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text=f"{language.language}", callback_data=f"get_language_anime_{anime.id}_{language.id}")]
                    for language in languages
                ]
            )
            result = await session.execute(select(User))
            users = result.scalars().all()

            count = 0
            for user in users:
                try:
                    await bot.send_photo(photo=anime.image, caption=await response_for_anime(anime=anime), reply_markup=inline_kb, chat_id=user.telegram_id)
                    count += 1
                except TelegramBadRequest:
                    pass
                except TelegramForbiddenError:
                    pass

            await state.clear()
            await message.answer(text=f"Muvaffqaiyatli yubrildi:{count} ", reply_markup=await admin_message_menu_def())
    except ValueError:
        await message.answer(text="raqamda yuboring", reply_markup=await cancel_keyboard())



@router.message(F.text == "🖼️ Rasmli habar",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_photo_message_as_message(message: types.Message, state: FSMContext):
    await state.set_state(GetImageMessage.photo)
    await message.answer(text="Rasmni yuboring tegida yozigi bilan!", reply_markup=await cancel_keyboard())


@router.message(GetImageMessage.photo, F.photo)
async def send_photo_message_process(message: types.Message, state: FSMContext, bot: Bot):
    image = message.photo[-1].file_id
    caption = message.caption
    if not caption:
        await message.answer(text="Caption siz rasm yubora olmaysiz!")
        return
    async with get_session() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
        if not users:
            await message.answer(text="Userlar yo'q", reply_markup=await cancel_keyboard())
            return
        count = 0
        for user in users:
            try:
                await bot.send_photo(photo=image, caption=caption, chat_id=user.telegram_id)
                count += 1
            except TelegramBadRequest:
                pass
            except TelegramForbiddenError:
                pass

        await state.clear()
        await message.answer("Muvaffaqiyatli yuborildi", reply_markup=await admin_message_menu_def())

@router.message(F.text == "🎥 Video bilan habar",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_video_message(message: types.Message, state: FSMContext):
    await state.set_state(GetVideoMessage.video)
    await message.answer(text="Videoni yuboring tegida yozigi bilan!", reply_markup=await cancel_keyboard())


@router.message(GetVideoMessage.video, F.video)
async def send_video_message_process(message: types.Message, state: FSMContext, bot: Bot):
    video = message.video.file_id
    caption = message.caption
    if not caption:
        await message.answer(text="Caption siz video yubora olmaysiz!")
        return
    async with get_session() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
        if not users:
            await message.answer(text="Userlar yo'q", reply_markup=await cancel_keyboard())
            return

        count = 0

        for user in users:
            try:
                await bot.send_video(video=video, caption=caption, chat_id=user.telegram_id)
                count += 1
            except TelegramBadRequest:
                pass
            except TelegramForbiddenError:
                pass

        await state.clear()
        await message.answer("Muvaffaqiyatli yuborildi", reply_markup=await admin_message_menu_def())

@router.message(F.text == "📎 Fayl yuborish",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_file_message(message: types.Message, state: FSMContext):
    await state.set_state(GetFileMessage.file)
    await message.answer(text="Fileni yuboring tegida yozigi bilan!", reply_markup=await cancel_keyboard())


@router.message(GetFileMessage.file, F.document)
async def send_file_message_process(message: types.Message, state: FSMContext, bot: Bot):
    file = message.document.file_id
    caption = message.caption

    if not caption:
        await message.answer(text="Caption siz file yubora olmaysiz!")
        return

    async with get_session() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
        if not users:
            await message.answer(text="Userlar yo'q", reply_markup=await cancel_keyboard())
            return

        count = 0

        for user in users:
            try:
                await bot.send_document(document=file, caption=caption, chat_id=user.telegram_id)
                count += 1
            except TelegramBadRequest:
                pass
            except TelegramForbiddenError:
                pass

        await state.clear()
        await message.answer("Muvaffaqiyatli yuborildi", reply_markup=await admin_message_menu_def())

@router.message(F.text == "🔁 Habarni forward qilish",
                F.chat.type == "private",
                AdminRoleFilter())
async def send_forward_message(message: types.Message, state: FSMContext):
    await state.set_state(GetForwardMessage.forward)
    await message.answer(text="Forward qilib yuboring:", reply_markup=await cancel_keyboard())


@router.message(GetForwardMessage.forward)
async def send_forward_message_process(message: types.Message, state: FSMContext, bot: Bot):
    await message.answer("Yuborish boshlandi. Iltimos, kuting...")
    asyncio.create_task(_background_forward_task(message, bot))
    await state.clear()


async def _background_forward_task(message: types.Message, bot: Bot):
    async with get_session() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()

        for user in users:
            try:
                await bot.forward_message(
                    chat_id=user.telegram_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
                await asyncio.sleep(0.6)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except (TelegramBadRequest, TelegramForbiddenError):
                continue