import math

from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Router, F, types, Bot
from config import  API_KEY
from routers.admin.role import AdminRoleFilter
from routers.database.database import get_session
from routers.database.models import get_animes, Anime, AnimeType, AnimeStatus, Admin
from routers.keyboards.keyboard import admin_settings_menu_def, user_main_menu_def, cancel_keyboard, \
    admin_main_menu_def, generate_pagination_markup, edit_anime_menu
from sqlalchemy import select, func
from text_form import generate_anime_list_text, response_for_anime
import aiohttp
router = Router()
IMGBB_API_KEY = API_KEY
async def upload_to_imgbb(bot: Bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    async with aiohttp.ClientSession() as session:
        # Rasmni Telegram'dan yuklab olish
        async with session.get(file_url) as resp:
            image_data = await resp.read()

        # FormData yasash (multipart/form-data)
        form = aiohttp.FormData()
        form.add_field('key', IMGBB_API_KEY)
        form.add_field('image', image_data, filename='image.jpg', content_type='image/jpeg')

        # imgBB ga so‘rov yuborish
        async with session.post('https://api.imgbb.com/1/upload', data=form) as resp:
            result = await resp.json()
            if result.get("success"):
                return result["data"]["url"]
            else:
                raise Exception("imgbb yuklashda xatolik: " + str(result))

class AnimeCreateState(StatesGroup):
    title = State()
    original_title = State()
    description = State()
    genre = State()
    type = State()
    status = State()
    release_date = State()
    end_date = State()
    studio = State()
    rating = State()
    score = State()
    count_episode = State()
    unique_id = State()
    image = State()
    save_anime = State()


# Echo (har qanday xabarni qaytarish)
@router.message(F.text == "🫀 Animeni sozlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def anime_settings(message: types.Message):
    await message.answer("⚙️ Anime sozlamalaridasiz" ,reply_markup=await admin_settings_menu_def())



@router.message(F.text == "➕ Anime qo'shish",
                F.chat.type == "private",
                AdminRoleFilter())
async def cmd_create(message: types.Message, state: FSMContext):
    await state.set_state(AnimeCreateState.title)
    await message.answer("📝 Anime nomini kiriting (1–200 belgidan):", reply_markup=await cancel_keyboard())

@router.message(F.text == "🚫 Bekor qilish")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    async with get_session() as session:
        admins = await session.execute(select(Admin))
        admins = admins.scalars.all()
        is_admin = False
        for admin in admins:
            if message.from_user.id == admin.telegram_id:
                is_admin = True
            else:
                is_admin = False
    kb = admin_main_menu_def() if is_admin else user_main_menu_def()
    await message.answer("✅ Jarayon bekor qilindi.", reply_markup=await kb)

@router.message(AnimeCreateState.title)
async def process_title(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not (1 <= len(text) <= 200):
        await message.answer("❗ 1–200 belgidan iborat nom kiriting:", reply_markup=await cancel_keyboard())
        return
    await state.update_data(title=text)
    await state.set_state(AnimeCreateState.original_title)
    await message.answer("📝 Original nomini kiriting (0–200 belgidan, bo‘sh qoldirish uchun “–” yuboring):")

@router.message(AnimeCreateState.original_title)
async def process_original_title(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text != "–" and len(text) > 200:
        await message.answer("❗ 0–200 belgidan iborat original nom kiriting:", reply_markup=await cancel_keyboard())
        return
    await state.update_data(original_title=None if text=="–" else text)
    await state.set_state(AnimeCreateState.description)
    await message.answer("🖊 Tavsifni kiriting (bo‘sh qoldirish uchun “–”):")

@router.message(AnimeCreateState.description)
async def process_description(message: types.Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(description=None if text=="–" else text)
    await state.set_state(AnimeCreateState.genre)
    await message.answer("🎭 Janrni kiriting (1–200 belgidan):")

@router.message(AnimeCreateState.genre)
async def process_genre(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not (1 <= len(text) <= 200):
        await message.answer("❗ 1–200 belgidan iborat janr kiriting:", reply_markup=await cancel_keyboard())
        return
    await state.update_data(genre=text)
    await state.set_state(AnimeCreateState.type)
    await message.answer("📺 Turini tanlang (TV, Movie, OVA, ONA, Special):")

@router.message(AnimeCreateState.type)
async def process_type(message: types.Message, state: FSMContext):
    key = message.text.strip()
    try:
        atype = AnimeType[key]
    except KeyError:
        await message.answer("❗ Qayta tanlang: TV, Movie, OVA, ONA yoki Special:", reply_markup=await cancel_keyboard())
        return
    await state.update_data(type=atype)
    await state.set_state(AnimeCreateState.status)
    await message.answer("📶 Statusini tanlang (Airing, Finished, Upcoming):")

@router.message(AnimeCreateState.status)
async def process_status(message: types.Message, state: FSMContext):
    key = message.text.strip()
    try:
        astatus = AnimeStatus[key]
    except KeyError:
        await message.answer("❗ Qayta tanlang: Airing, Finished yoki Upcoming:", reply_markup=await cancel_keyboard())
        return
    await state.update_data(status=astatus)
    await state.set_state(AnimeCreateState.release_date)
    await message.answer("🗓 Chiqqan sanasini kiriting (YYYY-MM-DD):")

@router.message(AnimeCreateState.release_date)
async def process_release_date(message: types.Message, state: FSMContext):
    from datetime import datetime
    text = message.text.strip()
    try:
        rd = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("❗ YYYY-MM-DD formatida bo‘lishi kerak:")
        return
    await state.update_data(release_date=str(rd))
    await state.set_state(AnimeCreateState.end_date)
    await message.answer("🏁 Tugagan sanani kiriting (YYYY-MM-DD yoki “–”):")

@router.message(AnimeCreateState.end_date)
async def process_end_date(message: types.Message, state: FSMContext):
    from datetime import datetime
    text = message.text.strip()
    if text == "–":
        ed = None
    else:
        try:
            ed = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            await message.answer("❗ YYYY-MM-DD formatida yoki “–” bo‘lsin:")
            return
        data = await state.get_data()
        release_date = datetime.strptime(data["release_date"], "%Y-%m-%d").date()
        if ed < release_date:
            await message.answer("❗ Tugash sanasi chiqish sanasidan keyin bo‘lishi kerak:")
            return
    await state.update_data(end_date=str(ed))
    await state.set_state(AnimeCreateState.studio)
    await message.answer("🏢 Studiya nomini kiriting (0–100 belgidan yoki “–”):")

@router.message(AnimeCreateState.studio)
async def process_studio(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text != "–" and len(text)>100:
        await message.answer("❗ 0–100 belgidan yoki “–” kiriting:")
        return
    await state.update_data(studio=None if text=="–" else text)
    await state.set_state(AnimeCreateState.rating)
    await message.answer("🔞 Reyting kiriting (0–20 belgidan yoki “–”):")

@router.message(AnimeCreateState.rating)
async def process_rating(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text!="–" and len(text)>20:
        await message.answer("❗ 0–20 belgidan yoki “–” kiriting:")
        return
    await state.update_data(rating=None if text=="–" else text)
    await state.set_state(AnimeCreateState.score)
    await message.answer("⭐️ Skor (butun son 0–100 yoki “–”):")

@router.message(AnimeCreateState.score)
async def process_score(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "–":
        score = None
    else:
        if not text.isdigit():
            await message.answer("❗ Butun son kiriting yoki “–”:")
            return
        score = int(text)
        if not (0 <= score <= 100):
            await message.answer("❗ 0–100 orasida bo‘lsin:")
            return
    await state.update_data(score=score)
    await state.set_state(AnimeCreateState.count_episode)
    await message.answer("🎬 Qismlar sonini kiriting (butun son):")

@router.message(AnimeCreateState.count_episode)
async def process_count_episode(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("❗ Butun son kiriting:")
        return
    cnt = int(text)
    await state.update_data(count_episode=cnt)
    await state.set_state(AnimeCreateState.unique_id)
    await message.answer("📔 Unikal kodini kiriting (butun son):")

@router.message(AnimeCreateState.unique_id)
async def process_unique_id(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("❗ Butun son kiriting:")
        return
    code = int(text)
    async with get_session() as session:
        res = await session.execute(select(Anime).where(Anime.unique_id==code))
        if res.scalar():
            await message.answer("❗ Bu kod allaqachon ishlatilgan:")
            return
    await state.update_data(unique_id=code)
    await state.set_state(AnimeCreateState.image)
    await message.answer("🖼 Rasm yuboring :")

@router.message(AnimeCreateState.image, F.photo)
async def process_image(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id

    # imgbb ga yuklash
    image_url = await upload_to_imgbb(message.bot, file_id)

    await state.update_data(image=image_url)
    await state.set_state(AnimeCreateState.save_anime)

    await message.answer("✅ Rasm imgbb.com'ga yuklandi!\n🔗 Link: " + image_url)
    await message.answer("✅ Barcha ma’lumot tayyor. “Ha” deb tasdiqlang yoki “🚫” bekor qiling.")

@router.message(AnimeCreateState.image)
async def invalid_image(message: types.Message, state: FSMContext):
    await message.answer("❗ Iltimos, rasm yuboring!")

@router.message(AnimeCreateState.save_anime, F.text)
async def finalize(message: types.Message, state: FSMContext):
    text = message.text.lower()
    if text in ["ha", "tasdiqlayman", "✅"]:
        data = await state.get_data()
        release_date = datetime.strptime(data["release_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        async with get_session() as session:
            anime = Anime(
                title=data["title"],
                original_title=data.get("original_title"),
                description=data.get("description"),
                genre=data["genre"],
                type=data["type"],
                status=data["status"],
                release_date=release_date,
                end_date=end_date,
                studio=data.get("studio"),
                rating=data.get("rating"),
                score=data.get("score"),
                count_episode=data["count_episode"],
                unique_id=data["unique_id"],
                image=data["image"]
            )
            session.add(anime)
            await session.commit()
        await message.answer("🎉 Anime muvaffaqiyatli qo‘shildi!", reply_markup=await admin_settings_menu_def())
        await state.clear()
    else:
        await message.answer("❌ Saqlash bekor qilindi.", reply_markup=await admin_main_menu_def())
        return
class ReadAnimeForm(StatesGroup):
    code = State()

@router.message(F.text == "👁 Animeni ko'zdan kechirish",
                F.chat.type == "private",
                AdminRoleFilter())
async def read_anime(message: types.Message, state: FSMContext):
    await state.set_state(ReadAnimeForm.code)
    await message.answer("Iltimos animeni kodini kiriting", reply_markup=await cancel_keyboard())

@router.message(ReadAnimeForm.code, F.text)
async def search_by_code(message: types.Message, state :FSMContext):
    try:
        code = int(message.text)
        async with get_session() as session:
            anime = await session.execute(select(Anime).where(Anime.unique_id == code))
            anime = anime.scalar()
            if not anime:
                await message.answer("Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
                return
            await message.answer_photo(photo=anime.image, caption=await response_for_anime(anime=anime),
                                       reply_markup=await admin_settings_menu_def())
            await state.clear()
    except ValueError:
        await message.answer("Iltimos kod kiriting", reply_markup=await cancel_keyboard())



@router.message(F.text == "👁 Barcha animelarni ko'rish",
                F.chat.type == "private",
                AdminRoleFilter())
async def show_all_animes(message: types.Message):
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

@router.callback_query(F.data.startswith("anime_page:"))
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

@router.message(F.text == "🗑 Animeni o'chirish",
                F.chat.type == "private",
                AdminRoleFilter())
async def process_delete_by_code(message: types.Message, state :FSMContext):
    await state.set_state(AnimeDeletionForm.code)
    await message.answer("Iltimos animeni o'chirish uchun kodini kiriting: ", reply_markup=await cancel_keyboard())




@router.message(AnimeDeletionForm.code, F.text)
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
        await message.answer(text="Iltimos o'chirmoqchi bo'lgan animeingizni kodini kiriting sonda :", reply_markup=await cancel_keyboard())

@router.message(F.text == "📝 Animeni tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def get_edit_keyboard(message: types.Message):
    await message.answer(text="Tanlang:", reply_markup=await edit_anime_menu())


@router.message(F.text == "📝 Nomi (name)ni tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_name(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforname.code)
    await message.answer(text="Animeni nomini o'zgartirish uchun anime kodini kiriting: ", reply_markup=await cancel_keyboard())

class AnimeEditname(StatesGroup):
    name = State()

@router.message(AnimeEditionFormforname.code, F.text)
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

@router.message(AnimeEditname.name, F.text)
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

@router.message(F.text == "🎭 Janrini (genre) tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_genre(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforgenre.code)
    await message.answer(text="Animeni janrini o'zgartirish uchun anime kodini kiriting: ", reply_markup=await cancel_keyboard())

class AnimeEditgenre(StatesGroup):
    genre = State()

@router.message(AnimeEditionFormforgenre.code, F.text)
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

@router.message(AnimeEditgenre.genre, F.text)
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


@router.message(F.text == "🎞 Qismlar sonini (count_episode) tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_count_episode(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforcount_episode.code)
    await message.answer(text="Animeni qismlar sonini o'zgartirish uchun anime kodini kiriting: ",
                         reply_markup=await cancel_keyboard())

class AnimeEditcount_episode(StatesGroup):
    count_episode = State()


@router.message(AnimeEditionFormforcount_episode.code, F.text)
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


@router.message(AnimeEditcount_episode.count_episode, F.text)
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
        await message.answer(text="Iltimos son qiymatida kirting: ", reply_markup=await cancel_keyboard())


@router.message(F.text == "🖼 Rasm (image) havolasini tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_image(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforimage.code)
    await message.answer(text="Animeni cover suratini o'zgartirish uchun anime kodini kiriting: ",
                         reply_markup=await cancel_keyboard())

class AnimeEditimage(StatesGroup):
    image = State()

@router.message(AnimeEditionFormforimage.code, F.text)
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

@router.message(AnimeEditimage.image, F.photo)
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


@router.message(AnimeEditimage.image)
async def invalidate_image_for_edit_anime(message: types.Message, state: FSMContext):
    await message.answer(text="Image yuboring", reply_markup=await cancel_keyboard())



# 5. Chiqarilish sanasini tahrirlash
@router.message(F.text == "📅 Chiqarilish sanasini (release_date) tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_release_date(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforrelease_date.code)
    await message.answer(
        text="Chiqarilish sanasini o'zgartirish uchun anime kodini kiriting (YYYY-MM-DD):",
        reply_markup=await cancel_keyboard()
    )

class AnimeEditionFormforrelease_date(StatesGroup):
    code = State()

class AnimeEditrelease_date(StatesGroup):
    release_date = State()

@router.message(AnimeEditionFormforrelease_date.code, F.text)
async def edit_for_release_date(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        if not anime:
            await message.answer("Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
            return
        await state.update_data(code=code)
        await state.set_state(AnimeEditrelease_date.release_date)
        await message.answer("Yangi chiqarilish sanasini kiriting (YYYY-MM-DD):", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer("Iltimos kodni raqamda kiriting", reply_markup=await cancel_keyboard())

@router.message(AnimeEditrelease_date.release_date, F.text)
async def release_date_process(message: types.Message, state: FSMContext):
    text = message.text.strip()
    try:
        new_date = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Format xato! Iltimos YYYY-MM-DD ko‘rinishda kiriting", reply_markup=await cancel_keyboard())
        return
    data = await state.get_data()
    code = data["code"]
    async with get_session() as session:
        anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        anime.release_date = new_date
        await session.commit()
    await message.answer("✅ Chiqarilish sanasi muvaffaqiyatli o'zgartirildi!", reply_markup=await admin_settings_menu_def())
    await state.clear()


# 6. Tugash sanasini tahrirlash
@router.message(F.text == "📅 Tugash sanasini (end_date) tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_end_date(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforend_date.code)
    await message.answer(
        text="Tugash sanasini o'zgartirish uchun anime kodini kiriting (YYYY-MM-DD):",
        reply_markup=await cancel_keyboard()
    )

class AnimeEditionFormforend_date(StatesGroup):
    code = State()

class AnimeEditend_date(StatesGroup):
    end_date = State()

@router.message(AnimeEditionFormforend_date.code, F.text)
async def edit_for_end_date(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        if not anime:
            await message.answer("Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
            return
        await state.update_data(code=code)
        await state.set_state(AnimeEditend_date.end_date)
        await message.answer("Yangi tugash sanasini kiriting (YYYY-MM-DD):", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer("Iltimos kodni raqamda kiriting", reply_markup=await cancel_keyboard())

@router.message(AnimeEditend_date.end_date, F.text)
async def end_date_process(message: types.Message, state: FSMContext):
    text = message.text.strip()
    try:
        new_date = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Format xato! Iltimos YYYY-MM-DD ko‘rinishda kiriting", reply_markup=await cancel_keyboard())
        return
    data = await state.get_data()
    code = data["code"]
    async with get_session() as session:
        anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        anime.end_date = new_date
        await session.commit()
    await message.answer("✅ Tugash sanasi muvaffaqiyatli o'zgartirildi!", reply_markup=await admin_settings_menu_def())
    await state.clear()


# 7. Reytingni tahrirlash
@router.message(F.text == "⭐ Reytingni (rating) tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_rating(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforrating.code)
    await message.answer(
        text="Reytingni o'zgartirish uchun anime kodini kiriting:",
        reply_markup=await cancel_keyboard()
    )

class AnimeEditionFormforrating(StatesGroup):
    code = State()

class AnimeEditrating(StatesGroup):
    rating = State()

@router.message(AnimeEditionFormforrating.code, F.text)
async def edit_for_rating(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        if not anime:
            await message.answer("Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
            return
        await state.update_data(code=code)
        await state.set_state(AnimeEditrating.rating)
        await message.answer("Yangi reytingni kiriting (maks 20 ta belgi):", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer("Iltimos kodni raqamda kiriting", reply_markup=await cancel_keyboard())

@router.message(AnimeEditrating.rating, F.text)
async def rating_process(message: types.Message, state: FSMContext):
    rating = message.text.strip()
    if len(rating) > 20:
        await message.answer("Belgilarning soni ortiqcha, qisqartiring", reply_markup=await cancel_keyboard())
        return
    data = await state.get_data()
    code = data["code"]
    async with get_session() as session:
        anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        anime.rating = rating
        await session.commit()
    await message.answer("✅ Reyting muvaffaqiyatli yangilandi!", reply_markup=await admin_settings_menu_def())
    await state.clear()


# 8. Baholashni tahrirlash
@router.message(F.text == "💯 Baholashni (score) tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_score(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforscore.code)
    await message.answer(
        text="Baholashni o'zgartirish uchun anime kodini kiriting:",
        reply_markup=await cancel_keyboard()
    )

class AnimeEditionFormforscore(StatesGroup):
    code = State()

class AnimeEditscore(StatesGroup):
    score = State()

@router.message(AnimeEditionFormforscore.code, F.text)
async def edit_for_score(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        if not anime:
            await message.answer("Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
            return
        await state.update_data(code=code)
        await state.set_state(AnimeEditscore.score)
        await message.answer("Yangi bahon ko‘rsatkichini kiriting (raqam):", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer("Iltimos kodni raqamda kiriting", reply_markup=await cancel_keyboard())

@router.message(AnimeEditscore.score, F.text)
async def score_process(message: types.Message, state: FSMContext):
    try:
        new_score = int(message.text.strip())
    except ValueError:
        await message.answer("Iltimos raqam kiriting", reply_markup=await cancel_keyboard())
        return
    data = await state.get_data()
    code = data["code"]
    async with get_session() as session:
        anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        anime.score = new_score
        await session.commit()
    await message.answer("✅ Baholash muvaffaqiyatli yangilandi!", reply_markup=await admin_settings_menu_def())
    await state.clear()


# 9. Studio nomini tahrirlash
@router.message(F.text == "🏢 Studio (studio)ni tahrirlash",
                F.chat.type == "private",
                AdminRoleFilter())
async def edit_by_code_for_studio(message: types.Message, state: FSMContext):
    await state.set_state(AnimeEditionFormforstudio.code)
    await message.answer(
        text="Studio nomini o'zgartirish uchun anime kodini kiriting:",
        reply_markup=await cancel_keyboard()
    )

class AnimeEditionFormforstudio(StatesGroup):
    code = State()

class AnimeEditstudio(StatesGroup):
    studio = State()

@router.message(AnimeEditionFormforstudio.code, F.text)
async def edit_for_studio(message: types.Message, state: FSMContext):
    try:
        code = int(message.text.strip())
        async with get_session() as session:
            anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        if not anime:
            await message.answer("Bu koddagi anime topilmadi", reply_markup=await cancel_keyboard())
            return
        await state.update_data(code=code)
        await state.set_state(AnimeEditstudio.studio)
        await message.answer("Yangi studio nomini kiriting (maks 100 belgigacha):", reply_markup=await cancel_keyboard())
    except ValueError:
        await message.answer("Iltimos kodni raqamda kiriting", reply_markup=await cancel_keyboard())

@router.message(AnimeEditstudio.studio, F.text)
async def studio_process(message: types.Message, state: FSMContext):
    studio = message.text.strip()
    if len(studio) > 100:
        await message.answer("Nom juda uzun, qisqartiring", reply_markup=await cancel_keyboard())
        return
    data = await state.get_data()
    code = data["code"]
    async with get_session() as session:
        anime = (await session.execute(select(Anime).where(Anime.unique_id == code))).scalar()
        anime.studio = studio
        await session.commit()
    await message.answer("✅ Studio nomi muvaffaqiyatli yangilandi!", reply_markup=await admin_settings_menu_def())
    await state.clear()


@router.message(F.text == "🔙 Anime sozlamalariga qaytish",
                F.chat.type == "private",
                AdminRoleFilter())
async def back_anime_settings_menu(message: types.Message):
    await message.answer(text="Qaytdingiz", reply_markup=await admin_settings_menu_def())
