import asyncio
import logging
from enum import unique
from ftplib import all_errors
import redis.asyncio as redis
from fastapi import FastAPI, Request
from sqlalchemy import select, func
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, \
    InlineQuery, InlineQueryResultPhoto, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import uvicorn
from sqlalchemy.util import await_fallback
from aiogram.utils.text_decorations import markdown_decoration as md
from text_form import response_for_anime, generate_anime_list_text
from keyboard import admin_main_menu_def, user_main_menu_def, cancel_keyboard, admin_post_menu_def, \
    admin_language_menu_def, admin_settings_menu_def, generate_pagination_markup, edit_anime_menu, edit_anime_series, \
    back_to_episode_settings, edit_language_keyboard
from database import get_session
from models import Anime, User, get_animes, AnimeLanguage, Episode, Channel, Post
from config import API_KEY
import math
import aiohttp

# Bot token (o'zingizning tokeningizni kiriting)
TOKEN = "8179305780:AAGFzN5cG8t1_hHETZcq-tIWri8VqZkaClo"

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# FastAPI ilovasini yaratamiz
app = FastAPI()
ADMINS = {5415350162}
# Bot va Dispatcher obyektlarini yaratamiz
bot = Bot(token=TOKEN,default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = ReplyKeyboardBuilder()
    user_id = message.from_user.id
    async with get_session() as session:
        exist_user = await session.execute(select(User).where(User.telegram_id==user_id))
        exist_user = exist_user.scalar()
        if not exist_user:
            username = message.from_user.username
            full_name = message.from_user.full_name
            if username:
                new_user = User(telegram_id=user_id, username=username, full_name=full_name)
            else:
                new_user = User(telegram_id=user_id, full_name=full_name)
            session.add(new_user)
            await session.commit()
    # Agar foydalanuvchi admin bo‘lsa
    if user_id in ADMINS:
        await message.answer("Botimga hush kelibman", reply_markup=await admin_main_menu_def())
    else:
        await message.answer("Botimga hush kelibsiz @iskurama", reply_markup=await user_main_menu_def())



class AnimeCreationForm(StatesGroup):
    name = State()
    genre = State()
    image = State()
    count_episode = State()
    code = State()

# Echo (har qanday xabarni qaytarish)
@dp.message(F.text == "🫀 Animeni sozlash")
async def anime_settings(message: types.Message):
    keyboard = ReplyKeyboardBuilder()
    if message.from_user.id in ADMINS:
        await message.answer("⚙️ Anime sozlamalaridasiz",reply_markup=await admin_settings_menu_def())
    else:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
    
@dp.message(F.text == "➕ Anime qo'shish")
async def create_anime(message: types.Message, state: FSMContext):
    await state.set_state(AnimeCreationForm.name)
    await message.answer("Salom! Animeni nomini yoki '🚫 Bekor qilish' tugmasini bosing:", 
                         reply_markup=await cancel_keyboard())

@dp.message(F.text == "🚫 Bekor qilish")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()  # ✅ FSM ni tozalash

    if message.from_user.id in ADMINS:
        await message.answer("Jarayon bekor qilindi. Endi boshqa buyruqlarni ishlatishingiz mumkin.", reply_markup=await admin_main_menu_def())
    else:
        await message.answer("Jarayon bekor qilindi. Endi boshqa buyruqlarni ishlatishingiz mumkin.", reply_markup=await user_main_menu_def())
    
@dp.message(AnimeCreationForm.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text
    if len(name) > 100:
        await message.answer(text="Iltimos ismini qisqaroq qiling",
                             reply_markup=await cancel_keyboard())
        return
    await state.update_data(name=name)
    await message.answer("🎭 Janrni kiriting yoki '🚫 Bekor qilish' tugmasini bosing:", 
                         reply_markup=await cancel_keyboard())
    await state.set_state(AnimeCreationForm.genre)

@dp.message(AnimeCreationForm.genre)
async def process_genre(message: types.Message, state: FSMContext):
    genre = message.text
    if len(genre) > 100:
        await message.answer(text="Iltimos janrini qisqartiring",
                             reply_markup=await cancel_keyboard())
        return
    await state.update_data(genre=message.text)
    await message.answer("🖼 Rasmini yuboring yoki '🚫 Bekor qilish' tugmasini bosing:", 
                         reply_markup=await cancel_keyboard())
    await state.set_state(AnimeCreationForm.image)
@dp.message(AnimeCreationForm.image, F.photo)
async def process_image(message: types.Message, state: FSMContext):
    await state.update_data(image_id=message.photo[-1].file_id)
    await message.answer("🟰 Qancha qismiga egaligini yozing yuboring yoki '🚫 Bekor qilish' tugmasini bosing:", 
                         reply_markup=await cancel_keyboard())
    await state.set_state(AnimeCreationForm.count_episode)
@dp.message(AnimeCreationForm.image)
async def invalidate_image(message: types.Message, state: FSMContext):
    await message.answer("⚠️ Iltimos, rasm yuboring!", reply_markup=await cancel_keyboard())

@dp.message(AnimeCreationForm.count_episode)
async def process_count_episode(message: types.Message, state: FSMContext):
    try:
        count_episodes = int(message.text)
        if count_episodes <= -2147483648 or count_episodes >= 2147483648:
            await message.answer(text="iltimos kichkinaroq son kiriting",
                                 reply_markup=await cancel_keyboard())
            return
        await state.update_data(count_episode=count_episodes)
        await message.answer("📔 Maxsus kodini yuboring yoki '🚫 Bekor qilish' tugmasini bosing:",
                         reply_markup=await cancel_keyboard())
        await state.set_state(AnimeCreationForm.code)
    except ValueError:
        await message.answer("Iltimos, sonda kiriting", reply_markup=await cancel_keyboard())


@dp.message(AnimeCreationForm.code)
async def process_code(message: types.Message, state: FSMContext):
    try:
        code = int(message.text)
        if code <= -2147483648 or code >= 2147483648:
            await message.answer(text="Iltimos kichkinaroq son kirting",
                                 reply_markup=await cancel_keyboard())
            return
        async with get_session() as session:
            exist_anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            exist_anime = exist_anime.scalar()
            if exist_anime:
                await message.answer(text="Bu kodda allaqchon anime mavjud",
                                     reply_markup=await cancel_keyboard())
                return
            user_data = await state.get_data()
            keyboard = ReplyKeyboardBuilder()
            anime_name = user_data.get("name")
            anime_genre = user_data.get("genre")
            anime_image_id = user_data.get("image_id")
            anime_count_episode = user_data.get("count_episode")
            anime = Anime(name=anime_name, genre=anime_genre, image=anime_image_id, count_episode=anime_count_episode, unique_id=code)
            session.add(anime)
            await session.commit()
            await message.answer("✅ Animeni qo'shdingiz! Tugmalardan foydalaning:",
                         reply_markup=await admin_settings_menu_def())
        await state.clear()
    except ValueError:
        await message.answer("Iltimos son qiymatida yuboring", reply_markup=await cancel_keyboard())

class ReadAnimeForm(StatesGroup):
    code = State()

@dp.message(F.text == "👁 Animeni ko'zdan kechirish")
async def read_anime(message: types.Message, state: FSMContext):
    if not message.from_user.id in ADMINS:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
        return
    await state.set_state(ReadAnimeForm.code)
    await message.answer("Iltimos animeni kodini kiriting", reply_markup=await cancel_keyboard())

@dp.message(ReadAnimeForm.code)
async def search_by_code(message: types.Message, state:FSMContext):
    try:
        code = int(message.text)
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer("Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
                return
            await message.answer_photo(photo=anime.image, caption=await response_for_anime(name=anime.name,
                                                                                           genre=anime.genre,
                                                                                           count_episodes=anime.count_episode,
                                                                                           unique_id=anime.unique_id),
                                       reply_markup=await admin_settings_menu_def())
            await state.clear()
    except ValueError:
        await message.answer("Iltimos kod kiriting", reply_markup=await cancel_keyboard())



@dp.message(F.text == "👁 Barcha animelarni ko'rish")
async def show_all_animes(message: types.Message):
    if not message.from_user.id in ADMINS:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
        return
    async with get_session() as session:
        page = 1
        limit = 15
        offset = (page - 1) * limit

        animes = await get_animes(session=session, offset=offset, limit=limit)
        result = await session.execute(select(func.count()).select_from(Anime))
        count = result.scalar()
        total_pages = math.ceil(count / limit)
        text = generate_anime_list_text(animes, page=page, total_pages=total_pages)
        markup = generate_pagination_markup(current_page=page, total_pages=total_pages)

        await message.answer(text, reply_markup=markup)

@dp.callback_query(F.data.startswith("anime_page:"))
async def handle_anime_pagination(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    limit = 15
    offset = (page - 1) * limit

    async with get_session() as session:
        animes = await get_animes(session=session, offset=offset, limit=limit)
        result = await session.execute(select(func.count()).select_from(Anime))
        count = result.scalar()
        total_pages = math.ceil(count / limit)

        text = generate_anime_list_text(animes, page, total_pages)
        markup = generate_pagination_markup(current_page=page, total_pages=total_pages)

        await callback.message.edit_text(text, reply_markup=markup)
        await callback.answer()

class AnimeDeletionForm(StatesGroup):
    code = State()

class AnimeEditionFormforname(StatesGroup):
    code = State()

class AnimeEditionFormforgenre(StatesGroup):
    code = State()

class AnimeEditionFormforcount_episode(StatesGroup):
    code = State()

class AnimeEditionFormforimage(StatesGroup):
    code = State()

@dp.message(F.text == "🗑 Animeni o'chirish")
async def process_delete_by_code(message: types.Message, state:FSMContext):
    if not message.from_user.id in ADMINS:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
        return
    await state.set_state(AnimeDeletionForm.code)
    await message.answer("Iltimos animeni o'chirish uchun kodini kiriting: ", reply_markup=await cancel_keyboard())

@dp.message(AnimeDeletionForm.code)
async def delete_anime_by_code(message: types.Message, state: FSMContext):
    try:
        code = int(message.text)
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer(text="Bunday kodli anime mavjud emas")
                return
            await session.delete(anime)
            await session.commit()
            await state.clear()
            await message.answer(text="✅ Anime o'chirildi", reply_markup=await admin_settings_menu_def())
    except ValueError:
        await message.answer(text="Iltimos o'chirmoqchi bo'lgan animeingizni kodini kiriting sonda :", reply_markup=await cancel_handler())

@dp.message(F.text == "📝 Animeni tahrirlash")
async def get_edit_keyboard(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer(text="Tanlang:", reply_markup=await edit_anime_menu())
    else:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())


@dp.message(F.text == "📝 Nomi (name)ni tahrirlash")
async def edit_by_code_for_name(message: types.Message, state: FSMContext):
    if not message.from_user.id in ADMINS:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
        return
    await state.set_state(AnimeEditionFormforname.code)
    await message.answer(text="Animeni nomini o'zgartirish uchun anime kodini kiriting: ", reply_markup=await cancel_keyboard())

class AnimeEditname(StatesGroup):
    name = State()

@dp.message(AnimeEditionFormforname.code)
async def edit_for_name(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer(text="Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
                return
            await state.set_state(AnimeEditname.name)
            await state.update_data(code=code)
            await message.answer(text="Iltimos o'zgartirmoqchi bo'lgan nomni kirting", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer(text="Iltimos kodni raqamda kiriting", reply_markup=await cancel_keyboard())

@dp.message(AnimeEditname.name)
async def name_process(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) > 100:
        await message.answer(text="Iltimos nomini qisqartirng", reply_markup=await cancel_keyboard())
        return
    user_data = await state.get_data()
    code = int(user_data.get("code"))
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.unique_id == code))
        anime = anime.scalar()
        anime.name = name
        await session.commit()
    await message.answer("✅ Anime nomi muvaffaqiyatli o'zgartirildi!", reply_markup=await admin_settings_menu_def())
    await state.clear()

@dp.message(F.text == "🎭 Janrini (genre) tahrirlash")
async def edit_by_code_for_genre(message: types.Message, state: FSMContext):
    if not message.from_user.id in ADMINS:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
        return
    await state.set_state(AnimeEditionFormforgenre.code)
    await message.answer(text="Animeni janrini o'zgartirish uchun anime kodini kiriting: ", reply_markup=await cancel_keyboard())

class AnimeEditgenre(StatesGroup):
    genre = State()

@dp.message(AnimeEditionFormforgenre.code)
async def edit_for_genre(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer(text="Bu kodda anime topilmadi ")
                return
            await state.set_state(AnimeEditgenre.genre)
            await state.update_data(code=code)
            await message.answer(text="Endi yangi janrlarini kirting: ", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer(text="Iltimos kodni sonda kirting: ", reply_markup=await cancel_keyboard())

@dp.message(AnimeEditgenre.genre)
async def genre_process(message: types.Message, state: FSMContext):
    genre = message.text.strip()
    if len(genre) > 100:
        await message.answer(text="Iltimos janrini qisqartiring: ", reply_markup=await cancel_keyboard())
        return
    user_data = await state.get_data()
    code = int(user_data.get("code"))
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.unique_id == code))
        anime = anime.scalar()
        anime.genre = genre
        await session.commit()
    await message.answer("✅ Anime janri muvaffaqiyatli o'zgartirildi!", reply_markup=await admin_settings_menu_def())
    await state.clear()


@dp.message(F.text == "🎞 Qismlar sonini (count_episode) tahrirlash")
async def edit_by_code_for_count_episode(message: types.Message, state: FSMContext):
    if not message.from_user.id in ADMINS:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
        return
    await state.set_state(AnimeEditionFormforcount_episode.code)
    await message.answer(text="Animeni qismlar sonini o'zgartirish uchun anime kodini kiriting: ",
                         reply_markup=await cancel_keyboard())

class AnimeEditcount_episode(StatesGroup):
    count_episode = State()


@dp.message(AnimeEditionFormforcount_episode.code)
async def edit_for_count_episode(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer(text="Bu kodga kino topilmadi", reply_markup=await cancel_keyboard())
                return
            await state.set_state(AnimeEditcount_episode.count_episode)
            await state.update_data(code=code)
            await message.answer(text="Endi yanigi qiymatni kiriting: ", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer(text="Ilimos kodni sonda kiriting: ", reply_markup=await cancel_keyboard())


@dp.message(AnimeEditcount_episode.count_episode)
async def count_episode_process(message: types.Message, state: FSMContext):
    try:
        count_episodes = int(message.text.strip())
        if count_episodes <= -2147483648 or count_episodes >= 2147483648:
            await message.answer(text="Iltimos normal sonda kirting: ")
            return
        user_data = await state.get_data()
        code = int(user_data.get("code"))
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            anime.count_episode = count_episodes
            await session.commit()
        await message.answer("✅ Anime qismlar soni muvaffaqiyatli o'zgartirildi!", reply_markup=await admin_settings_menu_def())
        await state.clear()
    except ValueError:
        await message.answer(text="Iltimos son qiymatida kirting: ", reply_markup=await cancel_handler())


@dp.message(F.text == "🖼 Rasm (image) havolasini tahrirlash")
async def edit_by_code_for_image(message: types.Message, state: FSMContext):
    if not message.from_user.id in ADMINS:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())
        return
    await state.set_state(AnimeEditionFormforimage.code)
    await message.answer(text="Animeni cover suratini o'zgartirish uchun anime kodini kiriting: ",
                         reply_markup=await cancel_keyboard())

class AnimeEditimage(StatesGroup):
    image = State()

@dp.message(AnimeEditionFormforimage.code)
async def edit_for_image(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer("Bunday anime topilmadi: ", reply_markup=await cancel_keyboard())
                return
            await state.set_state(AnimeEditimage.image)
            await state.update_data(code=code)
            await message.answer(text="Rasm yuboring", reply_markup=await cancel_keyboard())


    except ValueError:
        await message.answer(text="Iltimos sonda kirting", reply_markup=await cancel_keyboard())

@dp.message(AnimeEditimage.image, F.photo)
async def image_process(message: types.Message, state: FSMContext):
    image_id = message.photo[-1].file_id
    user_data = await state.get_data()
    code = user_data.get("code")
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.unique_id == code))
        anime = anime.scalar()
        anime.image = image_id
        await session.commit()
    await message.answer("✅ Anime rasmi muvaffaqiyatli o'zgartirildi!", reply_markup=await admin_settings_menu_def())
    await state.clear()


@dp.message(AnimeEditimage.image)
async def invalidate_image_for_edit_anime(message: types.Message, state: FSMContext):
    await message.answer(text="Image yuboring", reply_markup=await cancel_keyboard())

@dp.message(F.text == "🔙 Anime sozlamalariga qaytish")
async def back_anime_settings_menu(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer(text="Qaytdingiz", reply_markup=await admin_settings_menu_def())
    else:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())

@dp.message(F.text == "🌎 Animeni tlini sozlash")
async def anime_language_settings(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer("⚙️ Anime tlini sozlamalaridasiz", reply_markup=await admin_language_menu_def())
    else:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())

class AnimeAddLanguageForm(StatesGroup):
    code = State()
    language = State()
    description = State()

@dp.message(F.text == "➕ Animega til qo'shish")
async def add_language_def(message: types.Message, state: FSMContext):
    await state.set_state(AnimeAddLanguageForm.code)
    await message.answer(text="Iltimos til qo'shish uchun anime kodini kiriting: ", reply_markup=await cancel_keyboard())


@dp.message(AnimeAddLanguageForm.code)
async def anime_search_by_code_for_add_language(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer("Bu kodga kino mavjud emas", reply_markup=await cancel_keyboard())
            await state.update_data(code=code)
            await message.answer(text="Endi qo'shmoqchi bo'lgan tilizni kirting: ", reply_markup=await cancel_keyboard())
            await state.set_state(AnimeAddLanguageForm.language)
    except ValueError:
        await message.answer(text="Iltimos sonda kiriting: ", reply_markup= await cancel_keyboard())

@dp.message(AnimeAddLanguageForm.language)
async def set_language(message: types.Message, state: FSMContext):
    language = message.text.strip()
    if len(language) > 100:
        await message.answer(text="Iltimos qisqartiring: ", reply_markup=await cancel_keyboard())
        return
    await state.update_data(language=language)
    await message.answer(text="Endi til haqida yozing: ", reply_markup=await cancel_keyboard())
    await state.set_state(AnimeAddLanguageForm.description)

@dp.message(AnimeAddLanguageForm.description)
async def set_description(message: types.Message, state: FSMContext):
    description = message.text
    user_data = await state.get_data()
    code = int(user_data.get("code"))
    language = user_data.get("language")
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.unique_id == code))
        anime = anime.scalar()
        anime_language = AnimeLanguage(anime_id=anime.id, language=language, description=description)
        session.add(anime_language)
        await session.commit()
        await state.clear()
        await message.answer(text="✅ Qo'shildi til muvaffaqiyatli", reply_markup=await admin_language_menu_def())

class AnimeLanguageGetForm(StatesGroup):
    code = State()

@dp.message(F.text == "👁 Animeni tillarni ko'rish")
async def read_anime_language_process(message: types.Message, state: FSMContext):
    await state.set_state(AnimeLanguageGetForm.code)
    await message.answer(text="Animeni kodini kiriting: ", reply_markup=await cancel_keyboard())

@dp.message(AnimeLanguageGetForm.code)
async def read_anime_language(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
    except ValueError:
        await message.answer("Iltimos, faqat son kiriting.", reply_markup=await cancel_keyboard())
        return

    async with get_session() as session:
        result = await session.execute(select(Anime).where(Anime.unique_id == code))
        anime = result.scalar()

        if not anime:
            await message.answer("Bunday kodga ega anime topilmadi.", reply_markup=await cancel_keyboard())
            return

        langs_result = await session.execute(
            select(AnimeLanguage).filter(AnimeLanguage.anime_id == anime.id)
        )
        languages = langs_result.scalars().all()

        if not languages:
            await message.answer("Bu anime uchun tillar mavjud emas.", reply_markup=await cancel_keyboard())
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=lang.language,
                    callback_data=f"anime_lang_{anime.id}_{lang.id}"
                )] for lang in languages
            ]
        )

        await state.clear()
        await message.answer_photo(photo=anime.image, caption=await response_for_anime(name=anime.name, genre=anime.genre, count_episodes=anime.count_episode, unique_id=anime.unique_id), reply_markup=keyboard)


@dp.callback_query(F.data.startswith("anime_lang_"))
async def handle_language_choice(callback: CallbackQuery):
    data = callback.data  # Masalan: 'anime_lang_123_1'

    # Bu yerda split(“_”) 4 ta qismga ajratadi, demak shunaqa o‘zgartirish kerak:
    _, _, anime_id, lang_id = data.split("_")

    # int ga o‘gir
    anime_id = int(anime_id)
    lang_id = int(lang_id)
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await callback.message.answer(text="Anime topilmadi", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language.scalar()
        if not language:
            await callback.message.answer(text="Anime tili topilmadi", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return
        await callback.message.answer(f"Siz {language.language}-tilni tanladingiz. Anime nomi: {anime.name}, nima qilishni hohlaysiz?", reply_markup=await edit_anime_series(anime=anime, lang=language))
        await callback.answer()
        await callback.message.delete()

class AnimeSeriesaddForm(StatesGroup):
    episode_number = State()
    video = State()

@dp.callback_query(F.data.startswith("add_series_"))
async def handle_add_series(callback: CallbackQuery, state: FSMContext):
    _, _, anime_id, lang_id = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await callback.message.answer(text="Anime topilmadi", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language.scalar()
        if not language:
            await callback.message.answer(text="Anime tili topilmadi", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return

        await state.set_state(AnimeSeriesaddForm.episode_number)
        await state.update_data(anime_id=anime.id)
        await state.update_data(language=language.id)
        await callback.message.answer(f"📝 Yangi qism qo‘shish: Anime nomi = {anime.name}, Tili = {language.language}, qism raqamini kirting", reply_markup=await cancel_keyboard())
        await callback.answer()
        await callback.message.delete()

@dp.message(AnimeSeriesaddForm.episode_number)
async def process_add_series_episode_number(message: types.Message, state: FSMContext):
    try:
        episode_number = int(message.text.strip())
    except ValueError:
        await message.answer("Iltimos raqamda kiriting! ", reply_markup=await cancel_keyboard())
        return
    if episode_number <= 0:
        await message.answer("Qism raqami 0 yoki manfiy bo‘lmasligi kerak!", reply_markup=await cancel_keyboard())
        return
    user_data = await state.get_data()
    anime_id = user_data.get("anime_id")
    language_id = user_data.get("language")
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await message.answer("Bunday anime topilmadi", reply_markup=await admin_main_menu_def())
            await state.clear()
            return
        if episode_number > anime.count_episode:
            await message.answer("Animening jami qismlaridan yuqori bu qism", reply_markup=await cancel_keyboard())
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == language_id))
        language = language.scalar()
        existing_episode = await session.execute(
            select(Episode).where(
                Episode.anime_id == anime_id,
                Episode.language_id == language_id,
                Episode.episode_number == episode_number
            )
        )
        existing_episode = existing_episode.scalar()

        if existing_episode:
            await message.answer(
                f"{language.language} tilida {episode_number}-qism allaqachon qo‘shilgan!",
                reply_markup=await cancel_keyboard()
            )
            return
        await state.set_state(AnimeSeriesaddForm.video)
        await state.update_data(episode_number=episode_number)
        await message.answer("Iltimos video yuboring qism uchun", reply_markup=await cancel_keyboard())

@dp.message(AnimeSeriesaddForm.video, F.video)
async def process_add_series_video(message: types.Message, state: FSMContext):
    video_id = message.video.file_id
    user_data = await state.get_data()
    anime_id = user_data.get("anime_id")
    language = user_data.get("language")
    episode_number = user_data.get("episode_number")
    async with get_session() as session:
        episode = Episode(anime_id=anime_id, episode_number=episode_number, video_id=video_id, language_id=language)
        session.add(episode)
        await session.commit()
        await state.clear()
        await message.answer(text="Muvaffaqiyatli qo'shildi! ", reply_markup=await admin_language_menu_def())

class EpisodeNumberGet(StatesGroup):
    episode_number = State()

@dp.callback_query(F.data.startswith("delete_series_"))
async def handle_delete_series(callback: CallbackQuery, state: FSMContext):
    _,_, anime_id, lang_id = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await callback.message.answer(text="Anime topilmadi.", reply_markup=await admin_main_menu_def())
            await callback.answer()
            await callback.message.delete()
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language.scalar()
        if not language:
            await callback.message.answer(text="Til topilmadi", reply_markup=await admin_main_menu_def())
            await callback.answer()
            await callback.message.delete()
            return
        await state.set_state(EpisodeNumberGet.episode_number)
        await state.update_data(anime_id=anime.id)
        await state.update_data(lang_id=language.id)
        await callback.message.answer(f"Qism o‘chirish uchun qism raqamini yuboring: Anime nomi = {anime.name}, Tili = {language.language}", reply_markup=await cancel_keyboard())
        await callback.answer()
        await callback.message.delete()


@dp.message(EpisodeNumberGet.episode_number)
async def delete_episode(message: types.Message, state: FSMContext):
    try:
        episode_number = int(message.text.strip())
        if episode_number <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Iltimos, musbat son kiriting.", reply_markup=await cancel_keyboard())
        return

    user_data = await state.get_data()
    anime_id = user_data.get("anime_id")
    lang_id = user_data.get("lang_id")

    async with get_session() as session:
        anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime_result.scalar()
        if not anime:
            await message.answer("Anime mavjud emas.", reply_markup=await admin_main_menu_def())
            await state.clear()
            return

        lang_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = lang_result.scalar()
        if not language:
            await message.answer("Anime tili mavjud emas, o‘chirilgan bo‘lishi mumkin.", reply_markup=await admin_main_menu_def())
            await state.clear()
            return

        episode_result = await session.execute(
            select(Episode).where(
                Episode.anime_id == anime.id,
                Episode.language_id == language.id,
                Episode.episode_number == episode_number
            )
        )
        episode = episode_result.scalar()
        if not episode:
            await message.answer(f"{episode_number}-qism mavjud emas.", reply_markup=await cancel_keyboard())
            return

        await session.delete(episode)
        await session.commit()

        await message.answer("Qism muvaffaqiyatli o‘chirildi.", reply_markup=await admin_language_menu_def())
        await state.clear()

class EpisodeNumberRead(StatesGroup):
    episode_number = State()

@dp.callback_query(F.data.startswith("read_series_"))
async def handle_read_series(callback: CallbackQuery, state: FSMContext):
    _, _, anime_id, lang_id = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await callback.message.answer(text="Anime topilmadi.", reply_markup=await admin_main_menu_def())
            await callback.answer()
            await callback.message.delete()
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language.scalar()
        if not language:
            await callback.message.answer(text="Til topilmadi", reply_markup=await admin_main_menu_def())
            await callback.answer()
            await callback.message.delete()
            return
        await state.set_state(EpisodeNumberRead.episode_number)
        await state.update_data(anime_id=anime.id)
        await state.update_data(lang_id=language.id)
        await callback.message.answer(f"🎞 Qismlarni ko‘rish uchun qism raqamini yuboring: Anime = {anime.name}, Tili = {language.language}")
        await callback.answer()

@dp.message(EpisodeNumberRead.episode_number)
async def read_episode(message: types.Message, state: FSMContext):
    try:
        episode_number = int(message.text.strip())
        if episode_number <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Iltimos, musbat son kiriting.", reply_markup=await cancel_keyboard())
        return

    user_data = await state.get_data()
    anime_id = user_data.get("anime_id")
    lang_id = user_data.get("lang_id")

    async with get_session() as session:
        anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime_result.scalar()
        if not anime:
            await message.answer("Anime mavjud emas.", reply_markup=await admin_main_menu_def())
            await state.clear()
            return

        lang_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = lang_result.scalar()
        if not language:
            await message.answer("Anime tili mavjud emas, o‘chirilgan bo‘lishi mumkin.", reply_markup=await admin_main_menu_def())
            await state.clear()
            return

        episode_result = await session.execute(
            select(Episode).where(
                Episode.anime_id == anime.id,
                Episode.language_id == language.id,
                Episode.episode_number == episode_number
            )
        )
        episode = episode_result.scalar()
        if not episode:
            await message.answer(f"{episode_number}-qism mavjud emas.", reply_markup=await cancel_keyboard())
            return

        await message.answer_video(video=episode.video_id, caption=f"Anime: {anime.name} ,\n Tili {language.language} \n Qismi: {episode.episode_number}", reply_markup=await back_to_episode_settings(anime=anime, lang=language))
        await state.clear()

class AnimeLanguageEditForm(StatesGroup):
    code = State()

@dp.message(F.text == "📝 Animeni tilini tahrirlash")
async def edit_language_process(message: types.Message, state: FSMContext):
    await state.set_state(AnimeLanguageEditForm.code)
    await message.answer("Animeni kodini kiriting: ", reply_markup=await cancel_keyboard())

@dp.message(AnimeLanguageEditForm.code)
async def edit_language(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        if code < 0:
            await message.answer(text="Iltimos musbat son kiriting: ", reply_markup=await cancel_keyboard())
            return
    except ValueError:
        await message.answer("Animeni kodini raqamda kiriting: ", reply_markup=await cancel_keyboard())
        return
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.unique_id == code))
        anime = anime.scalar()
        langs_result = await session.execute(
            select(AnimeLanguage).filter(AnimeLanguage.anime_id == anime.id)
        )
        languages = langs_result.scalars().all()

        if not languages:
            await message.answer("Bu anime uchun tillar mavjud emas.", reply_markup=await cancel_keyboard())
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=lang.language,
                    callback_data=f"anime_edit_lang_{anime.id}_{lang.id}"
                )] for lang in languages
            ]
        )
        await state.clear()
        await message.answer_photo(photo=anime.image,
                                   caption=await response_for_anime(name=anime.name, genre=anime.genre,
                                                                    count_episodes=anime.count_episode,
                                                                    unique_id=anime.unique_id), reply_markup=keyboard)

@dp.callback_query(F.data.startswith("anime_edit_lang_"))
async def handle_anime_lang(callback: CallbackQuery):
    _,_,_, anime_id, lang_id = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)
    async with get_session() as session:
        anime = await  session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await callback.message.answer("Anime topilmadi!", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language.scalar()
        if not language:
            await callback.message.answer("Tili topilmadi!", reply_markup=await admin_main_menu_def())
        await callback.message.answer_photo(photo=anime.image, caption=f"{language.language} ni nimasini o'zgartirmoqchisiz? ", reply_markup=await edit_language_keyboard(anime=anime, lang=language))

class AnimeLanguageNewNameForm(StatesGroup):
    new_language_name = State()

@dp.callback_query(F.data.startswith("edit_language_name_"))
async def handle_edit_language_name(callback: CallbackQuery, state: FSMContext):
    _, _, _, anime_id, lang_id = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)
    async with get_session() as session:
        anime = await  session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await callback.message.answer("Anime topilmadi!", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language.scalar()
        if not language:
            await callback.message.answer("Tili topilmadi!", reply_markup=await admin_main_menu_def())

        await callback.message.answer(f"📝 Anime {anime.name} ning {language.language} uchun yangi qiymatni yuboring! ", reply_markup=await cancel_keyboard())
        await state.set_state(AnimeLanguageNewNameForm.new_language_name)
        await state.update_data(anime_id=anime.id)
        await state.update_data(lang_id=language.id)
        await callback.answer()
@dp.message(AnimeLanguageNewNameForm.new_language_name)
async def new_anime_language_def(message: types.Message, state: FSMContext):
    new_lang = message.text.strip()
    if len(new_lang) > 100:
        await message.answer("Iltimos nomini qisqartiring: ", reply_markup=await cancel_keyboard())
        return
    user_data = await state.get_data()
    anime_id = int(user_data.get("anime_id"))
    lang_id = int(user_data.get("lang_id"))
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await message.answer("Anime topilmadi! ", reply_markup=await admin_main_menu_def())
            await state.clear()
            return
        language = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language.scalar()
        if not language:
            await message.answer("Tili topiladi", reply_markup=await admin_main_menu_def())
            await state.clear()
            return
        language.language = new_lang
        await session.commit()
        await state.clear()
        await message.answer(text="O'zgartirildi", reply_markup=await admin_language_menu_def())

class AnimeLanguageNewDescriptionForm(StatesGroup):
    new_language_description = State()

@dp.callback_query(F.data.startswith("edit_language_description_"))
async def handle_edit_language_description(callback: CallbackQuery, state: FSMContext):
    _, _, _, anime_id, lang_id = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)

    async with get_session() as session:
        anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime_result.scalar()
        if not anime:
            await callback.message.answer("Anime topilmadi!", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return

        lang_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = lang_result.scalar()
        if not language:
            await callback.message.answer("Tili topilmadi!", reply_markup=await admin_main_menu_def())
            await callback.answer()
            return

        await callback.message.answer(
            f"📝 Anime <b>{anime.name}</b> ning <b>{language.language}</b> tili uchun yangi tavsifni yuboring!",
            reply_markup=await cancel_keyboard(),
            parse_mode="HTML"
        )

        await state.set_state(AnimeLanguageNewDescriptionForm.new_language_description)
        await state.update_data(anime_id=anime.id, lang_id=language.id)
        await callback.answer()


@dp.message(AnimeLanguageNewDescriptionForm.new_language_description)
async def new_anime_language_description_def(message: types.Message, state: FSMContext):
    new_description = message.text.strip()
    if len(new_description) > 1000:
        await message.answer("Iltimos, tavsifni qisqartiring (1000 ta belgidan kam):", reply_markup=await cancel_keyboard())
        return  # return qo‘shildi

    user_data = await state.get_data()
    anime_id = int(user_data.get("anime_id"))
    lang_id = int(user_data.get("lang_id"))

    async with get_session() as session:
        anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime_result.scalar()
        if not anime:
            await message.answer("Anime topilmadi!", reply_markup=await admin_main_menu_def())
            await state.clear()
            return

        lang_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = lang_result.scalar()
        if not language:
            await message.answer("Til topilmadi!", reply_markup=await admin_main_menu_def())
            await state.clear()
            return

        language.description = new_description
        await session.commit()  # to‘g‘rilandi
        await state.clear()
        await message.answer("✅ Tavsif muvaffaqiyatli o‘zgartirildi!", reply_markup=await admin_language_menu_def())

class Waiting_for_anime_code(StatesGroup):
    code = State()
    waiting_for_language_to_delete = State()

@dp.message(F.text == "🗑 Animega oid tilni o'chirish")
async def delete_language(message: types.Message, state: FSMContext):
    # Anime kodini olish
    await message.answer("Iltimos, animeni kodini kiriting :", reply_markup=await cancel_keyboard())
    await state.set_state(Waiting_for_anime_code.code)  # yangi state



@dp.message(Waiting_for_anime_code.code)
async def get_anime_by_code(message: types.Message, state: FSMContext):
    anime_code = int(message.text.strip())

    async with get_session() as session:
        anime_result = await session.execute(select(Anime).where(Anime.unique_id == anime_code))
        anime = anime_result.scalar()

        if not anime:
            await message.answer("Anime topilmadi! Iltimos, yana bir bor tekshirib ko'ring.", reply_markup=await cancel_keyboard())
            return

        # Tillarni olish
        lang_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.anime_id == anime.id))
        languages = lang_result.scalars().all()

        if not languages:
            await message.answer("Bu anime uchun tilda ma'lumotlar topilmadi!", reply_markup=await cancel_keyboard())
            return

        # Inline keyboard yaratish
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=language.language, callback_data=f"delete_language_{anime.id}_{language.id}")]
            for language in languages
        ])


        await message.answer(f"Anime: {anime.name} uchun tildan birini tanlang va o'chirishni amalga oshiring.",
                             reply_markup=keyboard)
        await state.set_state(Waiting_for_anime_code.waiting_for_language_to_delete)  # yangi state
        await state.clear()


@dp.callback_query(F.data.startswith("delete_language_"))
async def handle_delete_language(callback: CallbackQuery):
    _,_, anime_id, lang_id = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)

    async with get_session() as session:
        # Anime va tilni olish
        anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime_result.scalar()

        language_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language_result.scalar()

        if not anime or not language:
            await callback.message.answer("Anime yoki til topilmadi!", reply_markup=await cancel_keyboard())
            await callback.answer()
            return
        episodes = await session.execute(select(Episode).filter(Episode.language_id == language.id))
        episodes = episodes.scalars().all()
        # Tilni o'chirish
        for episode in episodes:
            await session.delete(episode)
        await session.delete(language)
        await session.commit()

        # Yangi ma'lumot bilan javob berish
        await callback.message.answer(f"✅ {anime.name} anime uchun {language.language} tili muvaffaqiyatli o'chirildi.")
        await callback.answer()



class AddChannelStates(StatesGroup):
    channel = State()
    channel_name = State()

# States for Delete Channel
class DeleteChannelStates(StatesGroup):
    channel = State()


# Admin Post Settings Menu Handler
@dp.message(F.text == "📮 Post sozlamalari")
async def post_settings(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer("⚙️ Post sozlamalaridasiz", reply_markup=await admin_post_menu_def())
    else:
        await message.answer("Tugmalardan foydalaning", reply_markup=await user_main_menu_def())

# Add Post Handlers
# 1) Kanal ID so‘rash
@dp.message(F.text == "➕ Post yuborish uchun qo'shish")
async def cmd_add_channel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Iltimos, kanal ID (raqam) kiriting:",
        reply_markup=await cancel_keyboard()
    )
    await state.set_state(AddChannelStates.channel)

# 2) Kanal ID kelganda – DBda tekshirish yoki nom so‘rash
@dp.message(AddChannelStates.channel)
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
@dp.message(AddChannelStates.channel_name)
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
@dp.message(F.text == "👁 Post uchun kanallarni ko'rish")
async def view_channels(message: types.Message):
    async with get_session() as session:
        result = await session.execute(select(Channel))
        channels = result.scalars().all()
    if not channels:
        await message.answer("Hech qanday kanal mavjud emas.", reply_markup=await admin_post_menu_def())
        return
    text = "Kanallar ro'yxati:\n" + "\n".join(
        f"ID: {ch.id}, Channel ID: {ch.channel_id}, Name: {ch.name}, Username: @{ch.username or 'none'}"
        for ch in channels
    )
    await message.answer(text, reply_markup=await admin_post_menu_def())

# Delete Channel Handlers
@dp.message(F.text == "🗑 Post uchun kanalni o'chirish")
async def cmd_delete_channel(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, o'chirmoqchi bo'lgan kanal ID kiriting:", reply_markup=await cancel_keyboard())
    await state.set_state(DeleteChannelStates.channel)

@dp.message(DeleteChannelStates.channel)
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
@dp.message(F.text == "📝 Post tayyorlash")
async def cmd_prepare_post(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Iltimos, post qilmoqchi bo‘lgan anime kodini (unique_id) kiriting:",
        reply_markup=await cancel_keyboard()
    )
    await state.set_state(WaitingForPost.anime_code)

# 2) Anime kodini qabul qilib, bazadan olish va kanallarni ko‘rsatish
@dp.message(WaitingForPost.anime_code)
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
                    callback_data=f"post_to_channel_{ch.id}"
                )
            ]
            for ch in channels
        ]
    )
    await message.answer(
        f"Anime: <b>{anime.name}</b>\nKanallardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(WaitingForPost.choose_channel)

# 3) Kanal tanlanganda postni yuborish
@dp.callback_query(F.data.startswith("post_to_channel_"))
async def process_channel_choice(callback: CallbackQuery, state: FSMContext):
    channel_db_id = int(callback.data.rsplit("_", 1)[-1])
    data = await state.get_data()
    anime_id = data.get("anime_id")

    async with get_session() as session:
        anime   = (await session.execute(select(Anime).where(Anime.id == anime_id))).scalar_one_or_none()
        channel = (await session.execute(select(Channel).where(Channel.id == channel_db_id))).scalar_one_or_none()

    if not anime or not channel:
        await callback.message.answer("Xatolik: anime yoki kanal topilmadi.")
        await callback.answer()
        return await state.clear()

    # Postni yuboramiz
    caption = (
        f"<b>{anime.name}</b>\n"
        f"Janr: {anime.genre}\n"
        f"Episodlar soni: {anime.count_episode}\n"
        f"ID: {anime.unique_id}"
    )
    msg = await bot.send_photo(
        chat_id=channel.channel_id,
        photo=anime.image,
        caption=caption,
        parse_mode="HTML"
    )

    # DB ga saqlaymiz
    async with get_session() as session:
        post = Post(channel_id=channel.id, anime_id=anime.id, message_id=msg.message_id)
        session.add(post)
        await session.commit()

    await callback.message.answer("✅ Post muvaffaqiyatli yuborildi va saqlandi.")
    await callback.answer()
    await state.clear()


@dp.message(F.text == "👤 Admin panelga qaytish")
async def statistics(message: types.Message):
    if message.from_user.id in ADMINS:
        await message.answer("Admin panelga qaytishingiz uchun iltimos tugmalardan foydalaning",
                             reply_markup=await admin_main_menu_def())
    else:
        await message.answer("Admin panelga qaytishingiz uchun iltimos tugmalardan foydalaning",
                             reply_markup=await user_main_menu_def())

# @dp.message()
# async def echo_message(message: types.Message):
#     keyboard = ReplyKeyboardBuilder()
#     if message.from_user.id in ADMINS:
#
#     else:
#
#     await message.answer("iltimos tugmalardan foydalaning", reply_markup=keyboard.as_markup(resize_keyboard=True))


async def upload_telegram_file_to_imgbb(bot: Bot, file_id: str) -> str:
    # Telegram'dan fayl URLsini olish
    file = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    async with aiohttp.ClientSession() as session:
        # Rasmni yuklab olish
        async with session.get(file_url) as resp:
            image_bytes = await resp.read()

        # ImBB API'ga rasmni yuklash
        upload_url = f"https://api.imgbb.com/1/upload?key={API_KEY}"
        data = aiohttp.FormData()
        data.add_field("image", image_bytes)

        async with session.post(upload_url, data=data) as resp:
            result = await resp.json()

        if result.get("success"):
            return result["data"]["url"]
        else:
            raise Exception("ImBB yuklashda xatolik: " + str(result))

@dp.inline_query(F.query)
async def inline_query_handler(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    async with get_session() as session:
        result = await session.execute(
            select(Anime).where(Anime.name.ilike(f"%{query_text}%")).limit(10)
        )
        animes = result.scalars().all()

    inline_results = []

    for anime in animes:
        cache_key = f"anime_{anime.id}_image"

        image_url = await redis_client.get(cache_key)
        if image_url is None:
            image_url = await upload_telegram_file_to_imgbb(bot, anime.image)
            await redis_client.setex(cache_key, 604800, image_url)  # 1 hafta

        inline_results.append(
            InlineQueryResultArticle(
                id=str(anime.id),
                title=anime.name,
                description=await response_for_anime(name=anime.name, genre=anime.genre, count_episodes=anime.count_episode, unique_id=anime.unique_id),
                thumbnail_url=image_url,
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f'<a href="{image_url}">&#8205;</a>'  # zero‑width space link
                        f"╭━━━•❁🔹❁•━━━╮\n"
                        f"🎬 Anime nomi: <b>{anime.name}</b>\n"
                        f"📝 Janri: <i>{anime.genre}</i>\n"
                        f"📺 Qismlar soni: <code>{anime.count_episode}</code>\n"
                        f"╰━━━•❁⛩❁•━━━╯"
                    ),
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
            )
        )

    await inline_query.answer(inline_results, cache_time=1)

WEBHOOK_HOST = 'https://d3a9-2a05-45c2-2014-6800-2f05-212e-c109-7af5.ngrok-free.app'  # Webhook URL manzili
WEBHOOK_PATH = '/webhook'  # Webhook endpoint
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH
# FastAPI endpointlari
@app.get("/status")
async def get_status():
    return {"status": "Bot ishlayapti!"}

@app.post("/webhook")
async def webhook(request: Request):
    json = await request.json()
    update = types.Update(**json)
    await dp.feed_webhook_update(bot=bot, update=update)
    return {"status": "ok"}

# Botni webhook rejimida ishga tushirish
async def on_start():
    # Webhookni o'rnatish
    await bot.set_webhook(WEBHOOK_URL)

# FastAPI va Aiogram parallel ishga tushirish
async def uvicorn_server():
    """FastAPI serverini ishga tushirish"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()  # `async` rejimda ishlatish

async def main():
    bot_task = asyncio.create_task(on_start())  # Botni webhook rejimida ishga tushirish
    api_task = asyncio.create_task(uvicorn_server())  # FastAPI serverini ishga tushirish
    await asyncio.gather(bot_task, api_task)  # Ikkisini parallel ishlatish

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())