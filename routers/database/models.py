from typing import Optional, List
from enum import Enum
from datetime import datetime, date

from aiogram import Bot
from aiogram.types import ChatMember
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession

from routers.database.database import AsyncSessionLocal
from sqlmodel import SQLModel, Field, Relationship, select
from sqlalchemy import Column, String, Text, Integer, Date, DateTime, Boolean, func, UniqueConstraint, BigInteger
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest


class AnimeType(str, Enum):
    TV = "TV"
    Movie = "Movie"
    OVA = "OVA"
    ONA = "ONA"
    Special = "Special"


class AnimeStatus(str, Enum):
    Airing = "Airing"
    Finished = "Finished"
    Upcoming = "Upcoming"


class Anime(SQLModel, table=True):
    __tablename__ = "animes"
    __table_args__ = (
        UniqueConstraint("unique_id", name="uq_anime_unique_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(..., max_length=200, index=True)
    original_title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None)
    genre: Optional[str] = Field(default=None, max_length=200, index=True)

    type: AnimeType = Field(
        default=AnimeType.TV,
        sa_column=Column("type", String(10)),
    )
    status: AnimeStatus = Field(
        default=AnimeStatus.Upcoming,
        sa_column=Column("status", String(10)),
    )

    release_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    studio: Optional[str] = Field(default=None, max_length=100)
    rating: Optional[str] = Field(default=None, max_length=20)
    score: Optional[int] = Field(default=None)
    count_episode: Optional[int] = Field(default=None)
    unique_id: int = Field(..., index=True)
    image: Optional[str] = Field(default=None, max_length=500)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False),
    )

    translations: List["AnimeLanguage"] = Relationship(back_populates="anime")
    episodes: List["Episode"] = Relationship(back_populates="anime")
    posts: List["Post"] = Relationship(back_populates="anime")


class AnimeLanguage(SQLModel, table=True):
    __tablename__ = "anime_languages"
    __table_args__ = (
        UniqueConstraint("anime_id", "language", name="uq_language_per_anime"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    anime_id: int = Field(foreign_key="animes.id", nullable=False)
    language: str = Field(..., max_length=10)
    description: Optional[str] = Field(default=None)

    anime: "Anime" = Relationship(back_populates="translations")
    episodes: List["Episode"] = Relationship(back_populates="language")


class Episode(SQLModel, table=True):
    __tablename__ = "episodes"
    __table_args__ = (
        UniqueConstraint(
            "anime_id", "language_id", "episode_number", name="uq_episode_lang_number"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    anime_id: int = Field(foreign_key="animes.id", nullable=False)
    language_id: int = Field(foreign_key="anime_languages.id", nullable=False)
    episode_number: int = Field(...)
    video_id: str = Field(..., max_length=255)

    anime: "Anime" = Relationship(back_populates="episodes")
    language: "AnimeLanguage" = Relationship(back_populates="episodes")


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("telegram_id", name="uq_user_telegram_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(sa_column=Column(BigInteger, unique=True))
    username: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False),
    )


class Channel(SQLModel, table=True):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("channel_id", name="uq_channel_channel_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(sa_column=Column(BigInteger, unique=True, nullable=False))
    name: str = Field(...)
    username: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), nullable=False),
    )

    posts: List["Post"] = Relationship(back_populates="channel")


class Post(SQLModel, table=True):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("message_id", name="uq_post_message_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channels.id", nullable=False)
    anime_id: int = Field(foreign_key="animes.id", nullable=False)
    message_id: int = Field(..., unique=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), nullable=False),
    )

    channel: "Channel" = Relationship(back_populates="posts")
    anime: "Anime" = Relationship(back_populates="posts")


class Admin(SQLModel, table=True):
    __tablename__ = "admins"
    __table_args__ = (
        UniqueConstraint("telegram_id", name="uq_admin_telegram_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(sa_column=Column(BigInteger, unique=True))
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_super_admin: bool = Field(default=False)
    password: str = Field(..., max_length=100)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), nullable=False),
    )


class RequiredChannel(SQLModel, table=True):
    __tablename__ = "required_channels"
    __table_args__ = (
        UniqueConstraint("channel_id", name="uq_required_channel_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(sa_column=Column(BigInteger, unique=True, nullable=False))
    username: Optional[str] = Field(default=None, max_length=100)
    name: str = Field(..., max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), nullable=False),
    )


async def get_animes(session: AsyncSessionLocal, offset: int = 0, limit: int = 10) -> List[Anime]:
    statement = select(Anime).offset(offset).limit(limit).order_by(Anime.created_at.desc())
    result = await session.execute(statement)
    return result.scalars().all()



async def check_subscription(user_id: int, community_chat_id: int, bot: Bot) -> bool:
    try:
        # Use the Bot API to get the chat member status
        chat_member: ChatMember = await bot.get_chat_member(community_chat_id, user_id)

        # Check if the user is subscribed (member status should be 'member' or 'administrator')
        return chat_member.status in ['member', 'administrator', 'creator']



    except TelegramBadRequest as e:

        print(f"check_subscription error for user {user_id} in chat {community_chat_id}: {e}")

        return False


# Asynchronous get_user function
async def get_user(chat_id: int, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).filter(User.telegram_id == chat_id))
    return result.scalar_one_or_none()  # `scalar_one_or_none()` to safely get the user or None

# Asynchronous add_user function
async def add_user(chat_id: int, db: AsyncSession) -> User:
    new_user = User(telegram_id=chat_id)
    db.add(new_user)
    await db.commit()  # `await` is used here to commit asynchronously
    await db.refresh(new_user)  # Refresh asynchronously after committing
    return new_user

# Asynchronous get_employee_by_chat_id function
async def get_employee_by_chat_id(chat_id: int, session: AsyncSession) -> bool:
    result = await session.execute(select(Admin).filter(Admin.telegram_id == chat_id))
    employee = result.scalar()
    return employee is not None

# Asynchronous user_exists function
async def user_exists(chat_id: int, session: AsyncSessionLocal) -> bool:
    result = await session.execute(select(User).filter(User.telegram_id == chat_id))
    user = result.scalar()  # Bu yerda bir nechta foydalanuvchi o‘rniga bitta foydalanuvchi qaytariladi
    return user is not None

# Asynchronous get_required_channels function
async def get_required_channels(db: AsyncSession) -> list:
    result = await db.execute(select(RequiredChannel).filter(RequiredChannel.is_active == True))
    return result.scalars().all()