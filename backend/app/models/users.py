from sqlalchemy import Column, TIMESTAMP, String, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(72), nullable=False)
    genre_preferences = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationships
    feedbacks = relationship("UserFeedback", back_populates="user", cascade="all, delete")
