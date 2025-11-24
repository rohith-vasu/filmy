from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.model_handlers.movie_handler import (
    MovieHandler,
    MovieCreate,
    MovieUpdate,
)
from app.model_handlers.user_handler import UserResponse
from app.routes import AppResponse
from app.core.db import get_global_db_session
from app.dependencies.auth import get_current_user

movie_router = APIRouter(prefix="/movies", tags=["Movies"])


# -----------------------------------
# 🎬 Create or Update Movie (Auth)
# -----------------------------------
@movie_router.post("/", response_model=AppResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_movie(
    movie_in: MovieCreate,
    db: Session = Depends(get_global_db_session),
    current_user: UserResponse = Depends(get_current_user),
):
    movie_handler = MovieHandler(db)
    existing = db.query(movie_handler.model).filter_by(tmdb_id=movie_in.tmdb_id).first()

    if existing:
        updated = movie_handler.update(existing.id, MovieUpdate(**movie_in.model_dump()))
        return AppResponse(
            status="success",
            message="Movie updated successfully",
            data=updated,
        )

    created = movie_handler.create(movie_in)
    return AppResponse(
        status="success",
        message="Movie created successfully",
        data=created,
    )

# -----------------------------------
# 🎬 Get Movies
# -----------------------------------
@movie_router.get("/", response_model=AppResponse)
async def get_movies(
    db: Session = Depends(get_global_db_session),
    limit: int = Query(50, le=500000),
):
    handler = MovieHandler(db)

    movies = handler.list_all(
        limit=limit,
    )

    return AppResponse(
        status="success",
        message="Movies retrieved successfully",
        data=movies,
    )


# -----------------------------------
# 🎬 Get Movie by TMDB ID (Public)
# -----------------------------------
@movie_router.get("/tmdb/{tmdb_id}", response_model=AppResponse)
async def get_movie_by_tmdb_id(
    tmdb_id: int,
    db: Session = Depends(get_global_db_session),
):
    movie_handler = MovieHandler(db)
    movie = movie_handler.get_by_tmdb_id(tmdb_id)

    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with TMDB ID {tmdb_id} not found")

    return AppResponse(
        status="success",
        message="Movie retrieved successfully",
        data=movie,
    )


# -----------------------------------
# 🎬 List / Explore Movies (Public)
# -----------------------------------
@movie_router.get("/explore", response_model=AppResponse)
async def explore_movies(
    db: Session = Depends(get_global_db_session),
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    title: Optional[str] = None,
    genre: Optional[str] = None,
    language: Optional[str] = None,
    release_year: Optional[int] = None,
    sort_by: Optional[str] = "popularity",
    order: Optional[str] = "desc", 
    search_bar: bool = Query(False),
):
    handler = MovieHandler(db)

    movies, total = handler.query_movies_paginated(
        page=page,
        limit=limit,
        title=title,
        genre=genre,
        language=language,
        release_year=release_year,
        sort_by=sort_by,
        order=order,
        search_bar=search_bar,
    )

    return AppResponse(
        status="success",
        message="Movies retrieved successfully",
        data={
            "movies": movies,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }
    )


# -----------------------------------
# 🎬 Update Movie by ID (Auth)
# -----------------------------------
@movie_router.patch("/{movie_id}", response_model=AppResponse)
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdate,
    db: Session = Depends(get_global_db_session),
    current_user: UserResponse = Depends(get_current_user),
):
    movie_handler = MovieHandler(db)
    updated = movie_handler.update(movie_id, movie_in)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")

    return AppResponse(
        status="success",
        message="Movie updated successfully",
        data=updated,
    )


# -----------------------------------
# 🎬 Delete Movie by ID (Auth)
# -----------------------------------
@movie_router.delete("/{movie_id}", response_model=AppResponse)
async def delete_movie(
    movie_id: int,
    db: Session = Depends(get_global_db_session),
    current_user: UserResponse = Depends(get_current_user),
):
    movie_handler = MovieHandler(db)
    deleted = movie_handler.delete(movie_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")

    return AppResponse(
        status="success",
        message="Movie deleted successfully",
        data=deleted,
    )