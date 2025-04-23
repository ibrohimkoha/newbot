from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from config import TOKEN
from redis.asyncio import Redis


from api.main import router
from routers.handlers import (anime_settings,
                              anime_language_settings,
                              anime_post_settings,
                              anime_language,
                              inline_mode_query,
                              start,
                              required_channel_setting,
                              statistika)
from routers.handlers.user import search_anime
from routers.middlewares.middlewares import CheckRequiredChannelsMiddleware
app = FastAPI()
app.include_router(router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # yoki faqat React ilovangizni kiriting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Redisga ulanamiz
redis = Redis(host="localhost", port=6379)
# Storage tayyorlaymiz
storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder())

# Bot va Dispatcher obyektlarini yaratamiz
bot = Bot(token=TOKEN,default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=storage)
dp.message.middleware(CheckRequiredChannelsMiddleware())


# Routerlarni shu yerda qo‘shasiz
dp.include_router(start.router)
dp.include_router(anime_settings.router)
dp.include_router(anime_language_settings.router)
dp.include_router(anime_post_settings.router)
dp.include_router(anime_language.router)
dp.include_router(inline_mode_query.router)
dp.include_router(required_channel_setting.router)
dp.include_router(statistika.router)
dp.include_router(search_anime.router)
