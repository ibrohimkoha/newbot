from typing import AsyncGenerator
import requests
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status

from config import API_KEY
from routers.database.database import get_session_for_api
from routers.database.models import Anime
from api.schemas.anime import AnimeCreationSchema



async def anime_creation_cmd(data: AnimeCreationSchema, session):
        # Anime haqida ma'lumot bilan qaytish
        anime = Anime(title=data.title,
                      original_title=data.original_title,
                      description=data.description,
                      genre=data.genre,
                      type=data.type,
                      status=data.status,
                      release_date=data.release_date,
                      end_date=data.end_date,
                      studio=data.studio,
                      rating=data.rating,
                      score=data.score,
                      count_episode=data.count_episode,
                      unique_id=data.unique_id,
                      image=data.image_url)
        session.add(anime)
        await session.commit()
        return HTTPException(detail="Anime muvaffaqiyatli yaratildi!", status_code=status.HTTP_201_CREATED)
