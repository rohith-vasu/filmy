from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from . import CRUDManager
from app.models.user_feedback import UserFeedback


from app.model_handlers.movie_handler import MovieResponse
from sqlalchemy.orm import joinedload

# ---------- Pydantic Schemas ----------
class UserFeedbackCreate(BaseModel):
    user_id: Optional[int] = Field(None, description="User ID providing feedback")
    movie_id: int = Field(..., description="Movie ID being rated")
    rating: Optional[float] = Field(None, ge=0.5, le=5, description="Rating 1–5")
    review: Optional[str] = Field(None, description="Review of the movie")
    status: Optional[str] = Field(None, description="status: 'watchlist'|'watched'")

class UserFeedbackUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=0.5, le=5)
    review: Optional[str] = None
    status: Optional[str] = None


class UserFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int
    rating: Optional[float]
    review: Optional[str]
    status: Optional[str]
    movie: Optional[MovieResponse] = None


# ---------- Handler ----------
class UserFeedbackHandler(CRUDManager[UserFeedback, UserFeedbackCreate, UserFeedbackUpdate, UserFeedbackResponse]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=UserFeedback, response_schema=UserFeedbackResponse)

    def create(self, obj_in: UserFeedbackCreate) -> UserFeedbackResponse:
        return super().create(obj_in)

    def read(self, id: int) -> UserFeedbackResponse:
        return super().read(id)
        
    def update(self, id: int, obj_in: UserFeedbackUpdate) -> UserFeedbackResponse:
        update_data = obj_in.dict(exclude_unset=True)

        feedback = (
            self._db.query(UserFeedback)
            .filter(UserFeedback.id == id)
            .first()
        )

        for field, value in update_data.items():
            setattr(feedback, field, value)

        self._db.commit()
        self._db.refresh(feedback)

        return UserFeedbackResponse.model_validate(feedback)

        
    def delete(self, id: int) -> dict:
        return super().delete(id)
    
    def list_all(self, skip: int = 0, limit: int = 20) -> List[UserFeedbackResponse]:
        return super().list_all(skip, limit)

    def bulk_create(self, feedback_list: List[UserFeedbackCreate]):
        objs = [self._model(**fb.dict()) for fb in feedback_list]
        self._db.bulk_save_objects(objs)
        self._db.commit()

    def get_by_user_movie(self, user_id: int, movie_id: int) -> Optional[UserFeedbackResponse]:
        """Get feedback by user and movie."""
        try:
            feedback = (
                self._db.query(UserFeedback)
                .options(joinedload(UserFeedback.movie))
                .filter(UserFeedback.user_id == user_id, UserFeedback.movie_id == movie_id)
                .first()
            )
            return UserFeedbackResponse.model_validate(feedback) if feedback else None
        except NoResultFound:
            return None

    def get_user_feedbacks(self, user_id: int) -> List[UserFeedbackResponse]:
        """List all feedbacks given by a user."""
        feedbacks = (
            self._db.query(UserFeedback)
            .options(joinedload(UserFeedback.movie))
            .filter(UserFeedback.user_id == user_id)
            .order_by(UserFeedback.updated_at.desc())
            .all()
        )
        return [UserFeedbackResponse.model_validate(fb) for fb in feedbacks]

    def get_movie_feedbacks(self, movie_id: int) -> List[UserFeedbackResponse]:
        """List all feedbacks for a movie."""
        feedbacks = self._db.query(UserFeedback).filter(UserFeedback.movie_id == movie_id).all()
        return [UserFeedbackResponse.model_validate(fb) for fb in feedbacks]

    def get_user_watchlist(self, user_id: int) -> List[UserFeedbackResponse]:
        """List all movies in user's watchlist."""
        feedbacks = (
            self._db.query(UserFeedback)
            .options(joinedload(UserFeedback.movie))
            .filter(UserFeedback.user_id == user_id, UserFeedback.status == "watchlist")
            .all()
        )
        return [UserFeedbackResponse.model_validate(fb) for fb in feedbacks]

    def get_user_stats(self, user_id: int, movie_handler) -> dict:
        """Return user watch statistics."""
        feedbacks = (
            self._db.query(UserFeedback)
            .filter(UserFeedback.user_id == user_id, UserFeedback.status == "watched")
            .all()
        )

        if not feedbacks:
            return {
                "total_watched": 0,
                "total_languages_watched": 0,
                "watched_this_month": 0,
                "watched_this_year": 0,
            }

        now = datetime.utcnow()

        total_watched = len(feedbacks)
        watched_this_month = 0
        watched_this_year = 0
        languages = set()

        for fb in feedbacks:
            movie = movie_handler.get_by_id(fb.movie_id)

            if movie and movie.original_language:
                languages.add(movie.original_language)

            # Month filter
            if fb.created_at.year == now.year and fb.created_at.month == now.month:
                watched_this_month += 1

            # Year filter
            if fb.created_at.year == now.year:
                watched_this_year += 1

        return {
            "total_watched": total_watched,
            "total_languages_watched": len(languages),
            "watched_this_month": watched_this_month,
            "watched_this_year": watched_this_year,
        }
        
