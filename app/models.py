# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from .database import Base

class APIKeys(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    user_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)

class Anime(Base):
    __tablename__ = "anime"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genre = Column(String)
    aired_date = Column(DateTime)
    synopsis = Column(String)
    studio = Column(String)
    episodes = Column(Integer)
    rating = Column(Float)
    image_url = Column(String)
