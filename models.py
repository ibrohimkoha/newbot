
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text, func, select
from sqlalchemy.orm import relationship
import datetime
from database import Base, AsyncSessionLocal
class Anime(Base):
    __tablename__ = 'animes'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    genre = Column(String(100), nullable=False)
    count_episode = Column(Integer, nullable=False)
    image = Column(String(255), nullable=False)
    unique_id = Column(BigInteger, nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    translations = relationship("AnimeLanguage", back_populates="anime")
    episodes = relationship("Episode", back_populates="anime")
    posts = relationship("Post", back_populates="anime")

class AnimeLanguage(Base):
    __tablename__ = 'languages_for_anime'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    anime_id = Column(BigInteger, ForeignKey('animes.id', ondelete="CASCADE"), nullable=False)
    language = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    anime = relationship("Anime", back_populates="translations")

class Episode(Base):
    __tablename__ = 'episodes_for_language'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    anime_id = Column(BigInteger, ForeignKey('animes.id', ondelete="CASCADE"), nullable=False)
    episode_number = Column(Integer, nullable=False)
    video_id = Column(String(255), nullable=False)
    language_id = Column(BigInteger, ForeignKey('languages_for_anime.id', ondelete="CASCADE"), nullable=False)

    anime = relationship("Anime", back_populates="episodes")
    language = relationship("AnimeLanguage")

class User(Base):
    __tablename__ = 'users_for_anime'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

class Channel(Base):
    __tablename__ = 'channels'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())

    posts = relationship("Post", back_populates="channel")

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_id = Column(BigInteger, ForeignKey('channels.id', ondelete="CASCADE"), nullable=False)
    anime_id = Column(BigInteger, ForeignKey('animes.id', ondelete="CASCADE"), nullable=False)
    message_id = Column(BigInteger, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    channel = relationship("Channel", back_populates="posts")
    anime = relationship("Anime", back_populates="posts")


async def get_animes(session: AsyncSessionLocal, offset: int = 0, limit: int = 10):
    stmt = select(Anime).offset(offset).limit(limit).order_by(Anime.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()