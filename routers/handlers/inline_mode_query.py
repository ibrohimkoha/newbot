from aiogram import Bot, F, Router
import aiohttp
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, \
    InlineKeyboardButton
from sqlalchemy import select
import redis.asyncio as redis
from config import API_KEY
from routers.database.database import get_session
from routers.database.models import Anime
from text_form import response_for_anime, response_for_anime_for_inline_mode

router = Router()

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)



@router.inline_query(F.query)
async def inline_query_handler(inline_query: InlineQuery, bot: Bot):
    query_text = inline_query.query.strip()

    async with get_session() as session:
        if query_text:
            result = await session.execute(
                select(Anime).where(Anime.title.ilike(f"%{query_text}%")).limit(10)
            )
        else:
            result = await session.execute(
                select(Anime).limit(10)  # yoki istasang .order_by(Anime.id.desc()) ham qo‘sh
            )
        animes = result.scalars().all()

    inline_results = []
    bot_info = await bot.get_me()
    for anime in animes:
        inline_results.append(
            InlineQueryResultArticle(
                id=str(anime.id),
                title=f"🔹 {anime.title} 🔹 ",
                description=await response_for_anime_for_inline_mode(anime),
                thumbnail_url=anime.image,
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f'<a href="{anime.image}">&#8205;</a>'
                        f"╭━━━⌈ 𝗔𝗡𝗜𝗠𝗘 𝗠𝗔’𝗟𝗨𝗠𝗢𝗧𝗜 ⌋━━━╮\n"
                        f"┃ 🏷 𝗡𝗼𝗺𝗶: <b>{anime.title}</b>\n"
                        f"┃ 🎭 𝗝𝗮𝗻𝗿: <i>{anime.genre}</i>\n"
                        f"┃ 🎞 𝗤𝗶𝘀𝗺𝗹𝗮𝗿 𝘀𝗼𝗻𝗶: <code>{anime.count_episode}</code>\n"
                        f"╰━━━━━━━━━━━━━━━━━━━━━━━╯"
                    ),
                    parse_mode="HTML",
                    disable_web_page_preview=False
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔹 Ko'rish 🔹",
                                          url=f"https://t.me/{bot_info.username}?start={anime.unique_id}")]
                ])
            )
        )
    await inline_query.answer(inline_results, cache_time=1)
