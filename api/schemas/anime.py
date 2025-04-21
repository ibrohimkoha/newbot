from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from api.types.anime import AnimeType, AnimeStatus
from datetime import date

class AnimeCreationSchema(BaseModel):
    title: str = Field(..., max_length=200)
    original_title: Optional[str] = Field(..., max_length=200)
    description: Optional[str]
    genre: Optional[str] = Field(..., max_length=200)
    type: AnimeType = AnimeType.TV
    status: AnimeStatus = AnimeStatus.Upcoming
    release_date: Optional[date]
    end_date: Optional[date]
    studio: Optional[str] = Field(..., max_length=100)
    rating: Optional[str] = Field(..., max_length=20)
    score: Optional[int]
    count_episode: Optional[int]
    unique_id: int
    image_url: HttpUrl