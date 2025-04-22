from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from django.templatetags.i18n import language
from sqlalchemy import select, desc

from routers.database.database import get_session
from routers.database.models import Anime, AnimeLanguage, Episode
from routers.keyboards.keyboard import cancel_keyboard, get_sort_buttons
from text_form import response_for_anime

router = Router()



@router.message(F.text == "🫀 Animelar")
async def get_anime(message: types.Message):
    await message.answer_photo(photo="https://ibb.co/1YMH3PjL",caption=f". .  ── •✧⛩✧• ──  . .• Animelarni biz bilan tomosha qilish yanada osonroq  o((≧ω≦ ))o", reply_markup=await get_sort_buttons())

class SearchAnimeCode(StatesGroup):
    code = State()

@router.callback_query(F.data == "sort_by_id")
async def sort_by_id(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Iltimos qidirmoqchi bo'lgan animeni kodini kirting: ", reply_markup=await cancel_keyboard())
    await callback.answer()
    await state.set_state(SearchAnimeCode.code)
#
@router.message(SearchAnimeCode.code, F.text)
async def process_sort_by_id(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        if code < 0:
            await message.answer(text="Anime topilmadi! ", reply_markup=await cancel_keyboard())
            return
    except ValueError:
        await message.answer(text="Animeni kodini raqamda kiriting! ", reply_markup=await cancel_keyboard())
        return

    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.unique_id == code))
        anime = anime.scalar()
        if not anime:
            await message.answer(text="Anime topilmadi! ", reply_markup=await cancel_keyboard())
            return
        languages = await session.execute(select(AnimeLanguage).filter(AnimeLanguage.anime_id == anime.id))
        languages = languages.scalars().all()
        if not languages:
            await message.answer(text="Anime topilmadi! ", reply_markup=await cancel_keyboard())
            return
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=f"{language.language}", callback_data=f"get_language_anime_{anime.id}_{language.id}")]
                for language in languages
            ]
        )
        await message.answer_photo(photo=anime.image, caption=await response_for_anime(anime=anime), reply_markup=inline_kb)
        await state.clear()

@router.callback_query(F.data == "sort_by_latest")
async def sort_by_latest_callback(callback: types.CallbackQuery):
    await callback.answer()  # Tugmani bosganlikka javob

    async with get_session() as session:
        result = await session.execute(
            select(Anime).order_by(desc(Anime.id)).limit(10)
        )
        animes = result.scalars().all()

    if not animes:
        await callback.message.delete()
        await callback.message.answer(text="Anime topilmadi! ")
        await callback.answer()
        return
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f"{anime.title}", callback_data=f"get_anime_by_{anime.id}")]
            for anime in animes
        ]
    )
    await callback.message.delete()
    await callback.message.answer(f"tanlang: ", reply_markup=inline_kb)
    await callback.answer()

@router.callback_query(F.data.startswith("get_anime_by_"))
async def get_anime_def(callback: types.CallbackQuery):
    _, _, _, anime_id = callback.data.split("_")
    anime_id = int(anime_id)
    async with get_session() as session:
        anime = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime.scalar()
        if not anime:
            await callback.message.delete()
            await callback.message.answer(text="Anime topilmadi! ", reply_markup=await cancel_keyboard())
            await callback.answer()
            return
        languages = await session.execute(select(AnimeLanguage).filter(AnimeLanguage.anime_id == anime.id))
        languages = languages.scalars().all()
        if not languages:
            await callback.message.delete()
            await callback.message.answer(text="Anime topilmadi! ", reply_markup=await cancel_keyboard())
            await callback.answer()
            return
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=f"{language.language}",
                                            callback_data=f"get_language_anime_{anime.id}_{language.id}")]
                for language in languages
            ]
        )
        await callback.message.delete()
        await callback.message.answer_photo(photo=anime.image, caption=await response_for_anime(anime=anime),
                                   reply_markup=inline_kb)
        await callback.answer()