from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from routers.database.database import get_session
from routers.database.models import User, Anime, AnimeLanguage
from routers.keyboards.keyboard import admin_main_menu_def, user_main_menu_def
from text_form import response_for_anime
from config import ADMINS

router = Router()

# /start komandasi argument bilan kelganda
@router.message(CommandStart(deep_link=True))
async def start_handler(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    # `message.get_args()` orqali start parametrini olamiz
    start_param = command.args

    try:
            anime_code = int(start_param)  # anime ID ni olish
            # Anime ID bilan bog'liq harakatlar
            async with get_session() as session:
                anime = await session.execute(select(Anime).where(Anime.unique_id == anime_code))
                anime = anime.scalar_one_or_none()
                if anime:
                    languages = await session.execute(select(AnimeLanguage).filter(AnimeLanguage.anime_id == anime.id))
                    languages = languages.scalars().all()
                    if languages:
                        inline_kb = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text=f"{lang.language}", callback_data=f"get_language_anime_{anime.id}_{lang.id}")]
                            for lang in languages
                        ]
                        )
                        await message.answer_photo(photo=anime.image, caption=await response_for_anime(anime=anime), reply_markup=inline_kb)
                        return
                    else:
                        await message.answer_photo(photo=anime.image,
                                                   caption=await response_for_anime(anime=anime))
                        return

                else:
                    if message.from_user.id in ADMINS:
                        await message.answer("Botimga hush kelibman", reply_markup=await admin_main_menu_def())
                        return
                    else:
                        await message.answer(f"Botga hush kelibsiz {message.from_user.first_name}", reply_markup=await user_main_menu_def())
                        return
    except ValueError:
            if message.from_user.id in ADMINS:
                await message.answer("Botimga hush kelibman", reply_markup=await admin_main_menu_def())
                return
            else:
                await message.answer(f"Botga hush kelibsiz {message.from_user.first_name}", reply_markup=await user_main_menu_def())
                return

@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    # Foydalanuvchini bazaga qo'shish
    user_id = message.from_user.id
    # Adminlarni tekshirish
    if user_id in ADMINS:
        await message.answer("Botimga hush kelibman", reply_markup=await admin_main_menu_def())
    else:
        await message.answer(f"Botga hush kelibsiz {message.from_user.first_name}", reply_markup=await user_main_menu_def())
