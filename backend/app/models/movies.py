from sqlalchemy import Column, TIMESTAMP, String, Text, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.base import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    overview = Column(Text)
    genres = Column(Text)
    original_language = Column(String(50))
    tagline = Column(Text)
    keywords = Column(Text)
    runtime = Column(Integer)
    popularity = Column(Float)
    poster_path = Column(Text)
    release_year = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    feedbacks = relationship("UserFeedback", back_populates="movie", cascade="all, delete")
