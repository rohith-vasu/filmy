from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.db import get_global_db_session
from app.services.recommendation_service import RecommendationService
from app.model_handlers.user_handler import UserResponse
from app.dependencies.auth import get_current_user
from app.routes import AppResponse

recommendation_router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@recommendation_router.get("/guest", response_model=AppResponse)
def guest_recommendations(
    genres: Optional[List[str]] = Query(None),
    examples: Optional[List[str]] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_global_db_session)
):
    service = RecommendationService(db)
    movies = service.guest_recommendations(genres=genres, examples=examples, limit=limit)
    return AppResponse(
        status="success",
        message="Guest recommendations",
        data=movies
    )

@recommendation_router.get("/personalized", response_model=AppResponse)
def personalized_recommendations(
    db: Session = Depends(get_global_db_session),
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(10),
):
    service = RecommendationService(db)
    movies = service.personalized_recommendations(current_user.id, limit=limit)
    return AppResponse(
        status="success",
        message="Personalized recommendations",
        data=movies
    )

@recommendation_router.get("/recent", response_model=AppResponse)
def recent_activity_recommendations(
    db: Session = Depends(get_global_db_session),
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(12),
):
    service = RecommendationService(db)
    movies = service.recommendations_based_on_recent_activity(current_user.id, limit=limit)
    return AppResponse(
        status="success",
        message="Recommendations based on recent activity",
        data=movies
    )

@recommendation_router.get("/recommend", response_model=AppResponse)
def search_recommendations(
    query_movies: Optional[List[str]] = Query(None),
    genres: Optional[List[str]] = Query(None),
    languages: Optional[List[str]] = Query(None),
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_global_db_session),
    current_user: Optional[UserResponse] = Depends(get_current_user),
):
    service = RecommendationService(db)
    movies = service.search_recommendations(
        user_id=current_user.id if current_user else None,
        query_movies=query_movies,
        genres=genres,
        languages=languages,
        year_min=year_min,
        year_max=year_max,
        limit=limit
    )
    return AppResponse(
        status="success",
        message="Search recommendations",
        data=movies
    )

@recommendation_router.get("/similar-movies", response_model=AppResponse)
def similar_movies(
    id: int = Query(..., description="Movie ID to find similar movies for"),
    limit: int = Query(10, description="Number of similar movies to return"),
    db: Session = Depends(get_global_db_session),
):
    service = RecommendationService(db)
    movies = service.similar_movies(movie_id=id, limit=limit)
    return AppResponse(
        status="success",
        message=f"Similar movies for ID {id}",
        data=movies
    )
