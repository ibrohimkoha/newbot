from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from routers.admin.role import AdminRoleFilter
from routers.database.database import get_session
from routers.database.models import Anime, AnimeLanguage, Episode
from routers.keyboards.keyboard import admin_language_menu_def, user_main_menu_def, cancel_keyboard, \
    admin_main_menu_def, back_to_episode_settings, edit_language_keyboard, edit_anime_series
from sqlalchemy import select, desc
from text_form import response_for_anime

router = Router()



@router.message(
    F.text == "🌎 Animeni tlini sozlash", F.chat.type == "private",
                AdminRoleFilter())
async def anime_language_settings(message: types.Message):
    await message.answer("⚙️ Anime tlini sozlamalaridasiz", reply_markup=await admin_language_menu_def())

class AnimeAddLanguageForm(StatesGroup):
    code = State()
    language = State()
    description = State()

@router.message(F.text == "➕ Animega til qo'shish", F.chat.type == "private",
                AdminRoleFilter())
async def add_language_def(message: types.Message, state: FSMContext):
    await state.set_state(AnimeAddLanguageForm.code)
    await message.answer(text="Iltimos til qo'shish uchun anime kodini kiriting: ", reply_markup=await cancel_keyboard())


@router.message(AnimeAddLanguageForm.code, F.text)
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

@router.message(AnimeAddLanguageForm.language, F.text)
async def set_language(message: types.Message, state: FSMContext):
    if message and message.text:
        language = message.text.strip()
    else:
        await message.answer("Noto‘g‘ri xabar turi. Matn yuboring.", reply_markup=await cancel_keyboard())
        return
    if len(language) > 100:
        await message.answer(text="Iltimos qisqartiring: ", reply_markup=await cancel_keyboard())
        return
    await state.update_data(language=language)
    await message.answer(text="Endi til haqida yozing: ", reply_markup=await cancel_keyboard())
    await state.set_state(AnimeAddLanguageForm.description)

@router.message(AnimeAddLanguageForm.description, F.text)
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

@router.message(F.text == "👁 Animeni tillarni ko'rish",
                F.chat.type == "private",
                AdminRoleFilter())
async def read_anime_language_process(message: types.Message, state: FSMContext):
    await state.set_state(AnimeLanguageGetForm.code)
    await message.answer(text="Animeni kodini kiriting: ", reply_markup=await cancel_keyboard())

@router.message(AnimeLanguageGetForm.code, F.text)
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
        await message.answer_photo(photo=anime.image, caption=await response_for_anime(anime=anime), reply_markup=keyboard)


@router.callback_query(F.data.startswith("anime_lang_"))
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
        await callback.message.answer(f"Siz {language.language}-tilni tanladingiz. Anime nomi: {anime.title}, nima qilishni hohlaysiz?", reply_markup=await edit_anime_series(anime=anime, lang=language))
        await callback.answer()
        await callback.message.delete()

class AddAnimeEpisodesForm(StatesGroup):
    video = State()


@router.callback_query(F.data.startswith("add_episodes_"))
async def handle_add_episodes(callback: CallbackQuery, state: FSMContext):
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
        await state.set_state(AddAnimeEpisodesForm.video)
        await state.update_data(anime_id=anime.id)
        await state.update_data(language=language.id)
        await callback.message.answer(
            f"📝 Yangi qism qo‘shish: Anime nomi = {anime.title}, Tili = {language.language}, qism raqamini kirting",
            reply_markup=await cancel_keyboard())
        await callback.answer()
        await callback.message.delete()


@router.message(AddAnimeEpisodesForm.video, F.video)
async def add_episode_def(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    anime_id = user_data.get("anime_id")
    language_id = user_data.get("language")

    async with get_session() as session:
        # Anime ni topamiz
        anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime_result.scalar()
        if not anime:
            await message.answer(text="Anime topilmadi", reply_markup=await admin_main_menu_def())
            return

        # Tilni topamiz
        language_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == language_id))
        language = language_result.scalar()
        if not language:
            await message.answer(text="Anime tili topilmadi", reply_markup=await admin_main_menu_def())
            return

        # Oxirgi qism raqamini aniqlaymiz
        last_episode_result = await session.execute(
            select(Episode)
            .where(Episode.anime_id == anime_id, Episode.language_id == language_id)
            .order_by(desc(Episode.episode_number))
        )
        last_episode = last_episode_result.scalars().first()
        next_episode_number = (last_episode.episode_number if last_episode else 0) + 1

        # Faylni saqlaymiz (video_id orqali)
        new_episode = Episode(
            anime_id=anime_id,
            language_id=language_id,
            episode_number=next_episode_number,
            video_id=message.video.file_id,
        )
        session.add(new_episode)
        await session.commit()

        await message.answer(
            text=f"✅ {anime.title} ({language.language}) uchun {next_episode_number}-qism muvaffaqiyatli qo‘shildi! Yana qo'shing",
            reply_markup=await cancel_keyboard()
        )

        await state.clear()
        await state.set_state(AddAnimeEpisodesForm.video)
        await state.update_data(anime_id=anime.id)
        await state.update_data(language=language.id)


class AnimeSeriesaddForm(StatesGroup):
    episode_number = State()
    video = State()

@router.callback_query(F.data.startswith("add_series_"))
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
        await callback.message.answer(f"📝 Yangi qism qo‘shish: Anime nomi = {anime.title}, Tili = {language.language}, qism raqamini kirting", reply_markup=await cancel_keyboard())
        await callback.answer()
        await callback.message.delete()

@router.message(AnimeSeriesaddForm.episode_number, F.text)
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

@router.message(AnimeSeriesaddForm.video, F.video)
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

@router.callback_query(F.data.startswith("delete_series_"))
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
        await callback.message.answer(f"Qism o‘chirish uchun qism raqamini yuboring: Anime nomi = {anime.title}, Tili = {language.language}", reply_markup=await cancel_keyboard())
        await callback.answer()
        await callback.message.delete()


@router.message(EpisodeNumberGet.episode_number, F.text)
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

@router.callback_query(F.data.startswith("read_series_"))
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
        await callback.message.answer(f"🎞 Qismlarni ko‘rish uchun qism raqamini yuboring: Anime = {anime.title}, Tili = {language.language}")
        await callback.answer()

@router.message(EpisodeNumberRead.episode_number, F.text)
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

        await message.answer_video(video=episode.video_id, caption=f"Anime: {anime.title} ,\n Tili {language.language} \n Qismi: {episode.episode_number}", reply_markup=await back_to_episode_settings(anime=anime, lang=language))
        await state.clear()

class AnimeLanguageEditForm(StatesGroup):
    code = State()

@router.message(F.text == "📝 Animeni tilini tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_language_process(message: types.Message, state: FSMContext):
    await state.set_state(AnimeLanguageEditForm.code)
    await message.answer("Animeni kodini kiriting: ", reply_markup=await cancel_keyboard())

@router.message(AnimeLanguageEditForm.code, F.text)
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
                                   caption=await response_for_anime(anime=anime), reply_markup=keyboard)

@router.callback_query(F.data.startswith("anime_edit_lang_"))
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

@router.callback_query(F.data.startswith("edit_language_name_"))
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

        await callback.message.answer(f"📝 Anime {anime.title} ning {language.language} uchun yangi qiymatni yuboring! ", reply_markup=await cancel_keyboard())
        await state.set_state(AnimeLanguageNewNameForm.new_language_name)
        await state.update_data(anime_id=anime.id)
        await state.update_data(lang_id=language.id)
        await callback.answer()

@router.message(AnimeLanguageNewNameForm.new_language_name, F.text)
async def new_anime_language_def(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos nomini yuboring: ", reply_markup=await cancel_keyboard())
        return
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

@router.callback_query(F.data.startswith("edit_language_description_"))
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


@router.message(AnimeLanguageNewDescriptionForm.new_language_description, F.text)
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

@router.message(F.text == "🗑 Animega oid tilni o'chirish",
                F.chat.type == "private",
                AdminRoleFilter())
async def delete_language(message: types.Message, state: FSMContext):
    # Anime kodini olish
    await message.answer("Iltimos, animeni kodini kiriting :", reply_markup=await cancel_keyboard())
    await state.set_state(Waiting_for_anime_code.code)  # yangi state



@router.message(Waiting_for_anime_code.code)
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


        await message.answer(f"Anime: {anime.title} uchun tildan birini tanlang va o'chirishni amalga oshiring.",
                             reply_markup=keyboard)
        await state.set_state(Waiting_for_anime_code.waiting_for_language_to_delete)  # yangi state
        await state.clear()


@router.callback_query(F.data.startswith("delete_language_"))
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
        await callback.message.answer(f"✅ {anime.title} anime uchun {language.language} tili muvaffaqiyatli o'chirildi.")
        await callback.answer()



class AddChannelStates(StatesGroup):
    channel = State()
    channel_name = State()

# States for Delete Channel
class DeleteChannelStates(StatesGroup):
    channel = State()

