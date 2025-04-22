from contextlib import suppress

from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import F, Router

from routers.database.database import get_session
from sqlalchemy import select
from routers.database.models import Anime, AnimeLanguage, Episode
from routers.keyboards.keyboard import admin_main_menu_def, user_main_menu_def
from config import ADMINS

router = Router()

@router.callback_query(F.data.startswith("get_language_anime_"))
async def get_anime(callback: CallbackQuery):
    _, _, _, anime_id, lang_id, *page = callback.data.split("_")
    anime_id = int(anime_id)
    lang_id = int(lang_id)
    page_number = int(page[0]) if page else 1
    episodes_per_page = 15
    start_index = (page_number - 1) * episodes_per_page
    end_index = start_index + episodes_per_page

    async with get_session() as session:
        anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
        anime = anime_result.scalar()
        if not anime:
            await callback.message.delete()
            markup = await admin_main_menu_def() if callback.from_user.id in ADMINS else await user_main_menu_def()
            await callback.message.answer("🧐 Anime topilmadi! ", reply_markup=markup)
            with suppress(Exception):
                await callback.answer()
            return

        language_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
        language = language_result.scalar()
        if not language:
            await callback.message.delete()
            markup = await admin_main_menu_def() if callback.from_user.id in ADMINS else await user_main_menu_def()
            await callback.message.answer("🧐 Til topilmadi! ", reply_markup=markup)
            with suppress(Exception):
                await callback.answer()
            return

        episodes_result = await session.execute(
            select(Episode).where(
                Episode.language_id == language.id,
                Episode.anime_id == anime.id
            ).order_by(Episode.episode_number.asc())
        )
        series = episodes_result.scalars().all()

        if not series:
            await callback.message.delete()
            await callback.message.answer("🎥 Bu til uchun hech qanday qism yo‘q.")
            with suppress(Exception):
                await callback.answer()
            return

        page_episodes = series[start_index:end_index]
        if not page_episodes:
            await callback.message.answer("❌ Bu sahifa mavjud emas.")
            with suppress(Exception):
                await callback.answer()
            return

        inline_buttons = []
        for episode in page_episodes:
            text = f"▶️ {episode.episode_number}" if episode == page_episodes[0] else f"{episode.episode_number}"
            inline_buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"get_anime_list_{anime.id}_{language.id}_{episode.episode_number}_{page_number}"
                )
            )

        # Sahifalash tugmalari
        pagination_buttons = []
        if page_number > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"get_language_anime_{anime.id}_{language.id}_{page_number - 1}")
            )
        if end_index < len(series):
            pagination_buttons.append(
                InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"get_language_anime_{anime.id}_{language.id}_{page_number + 1}")
            )

        chunk_size = 3
        inline_keyboards = [
            inline_buttons[i:i + chunk_size] for i in range(0, len(inline_buttons), chunk_size)
        ]
        if pagination_buttons:
            inline_keyboards.append(pagination_buttons)

        inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboards)

        try:
            await callback.message.delete()  # Eski xabarni o‘chirishga urinish
        except Exception:
            pass  # Agar xabar allaqachon o‘chirilgan bo‘lsa

        await callback.message.answer_video(
            video=page_episodes[0].video_id,
            caption=f"{anime.title}\n\nSahifa: {page_number}",
            reply_markup=inline_kb
        )

        with suppress(Exception):
            await callback.answer()

@router.callback_query(F.data.startswith("get_anime_list_"))
async def get_anime_episode(callback: CallbackQuery):
    try:
        _,_, _, anime_id, lang_id, episode_number, page_number = callback.data.split("_")
        anime_id = int(anime_id)
        lang_id = int(lang_id)
        episode_number = int(episode_number)
        page_number = int(page_number)
        async with get_session() as session:
            anime_result = await session.execute(select(Anime).where(Anime.id == anime_id))
            anime = anime_result.scalar()
            if not anime:
                markup = await admin_main_menu_def() if callback.from_user.id in ADMINS else await user_main_menu_def()
                await callback.message.answer("Anime topilmadi ❌", reply_markup=markup)
                await callback.answer()
                return

            lang_result = await session.execute(select(AnimeLanguage).where(AnimeLanguage.id == lang_id))
            language = lang_result.scalar()
            if not language:
                markup = await admin_main_menu_def() if callback.from_user.id in ADMINS else await user_main_menu_def()
                await callback.message.answer("Til topilmadi ❌", reply_markup=markup)
                await callback.answer()
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
                markup = await admin_main_menu_def() if callback.from_user.id in ADMINS else await user_main_menu_def()
                await callback.message.answer("Bu epizod topilmadi ❌",reply_markup=markup)
                await callback.answer()
                return

            await callback.message.answer_video(
                video=episode.video_id,
                caption=f"{anime.title} - {episode.episode_number}"

            )

            with suppress(Exception):
                await callback.answer()

    except Exception as e:
        print(f"Xatolik: {e}")
        await callback.answer("Nomaʼlum xatolik yuz berdi ❌", show_alert=True)
