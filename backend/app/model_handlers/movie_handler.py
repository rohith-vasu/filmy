from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_

from . import CRUDManager
from app.models.movies import Movie


# ---------- Pydantic Schemas ----------
class MovieCreate(BaseModel):
    tmdb_id: int = Field(..., description="TMDB ID of the movie")
    title: str = Field(..., description="Title of the movie")
    overview: Optional[str] = None
    genres: Optional[str] = Field(default_factory="")
    original_language: Optional[str] = None
    tagline: Optional[str] = None
    keywords: Optional[str] = None
    runtime: Optional[int] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    release_year: Optional[int] = None


class MovieUpdate(BaseModel):
    tmdb_id: Optional[int] = None
    title: Optional[str] = None
    overview: Optional[str] = None
    genres: Optional[str] = Field(default_factory="")
    original_language: Optional[str] = None
    tagline: Optional[str] = None
    keywords: Optional[str] = None
    runtime: Optional[int] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    release_year: Optional[int] = None


class MovieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    title: str
    overview: Optional[str]
    genres: Optional[str]
    original_language: Optional[str]
    tagline: Optional[str]
    keywords: Optional[str]
    runtime: Optional[int]
    popularity: Optional[float]
    poster_path: Optional[str]
    release_year: Optional[int]
    created_at: datetime
    updated_at: datetime


# ---------- Handler ----------
class MovieHandler(CRUDManager[Movie, MovieCreate, MovieUpdate, MovieResponse]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Movie, response_schema=MovieResponse)

    def create(self, obj_in: MovieCreate) -> MovieResponse:
        return super().create(obj_in)

    def read(self, id: int) -> MovieResponse:
        return super().read(id)

    def update(self, id: int, obj_in: MovieUpdate) -> MovieResponse:
        return super().update(id, obj_in)

    def delete(self, id: int) -> dict:
        return super().delete(id)

    def list_all(self, skip: int = 0, limit: int = 20) -> List[MovieResponse]:
        return super().list_all(skip, limit)

    def get_by_title(self, title: str) -> Optional[MovieResponse]:
        """Retrieve a movie by title."""
        try:
            # movie = self._db.query(Movie).filter(Movie.title.ilike(f"{title}%")).first()
            movie = self._db.query(Movie).filter(Movie.title.ilike(title)).first()
            return MovieResponse.model_validate(movie) if movie else None
        except NoResultFound:
            return None

    def get_by_tmdb_id(self, tmdb_id: int) -> Optional[MovieResponse]:
        """Retrieve a movie by TMDB ID."""
        movie = self._db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
        return MovieResponse.model_validate(movie) if movie else None

    def get_by_id(self, id: int) -> Optional[MovieResponse]:
        """Return SQLAlchemy movie model object."""
        movie = self._db.query(Movie).filter(Movie.id == id).first()
        return MovieResponse.model_validate(movie) if movie else None

    def get_by_genres(self, genres: List[str], limit: int = 10) -> List[MovieResponse]:
        """Retrieve movies by genres."""
        movies = (
                self._db.query(Movie)
                .filter(Movie.runtime >= 60)
                .filter(
                    or_(*[Movie.genres.ilike(f"%{genre}%") for genre in genres[:3]])
                )
                .order_by(Movie.popularity.desc())
                .limit(limit)
            )
        return [MovieResponse.model_validate(m) for m in movies]


    def query_movies_paginated(
        self,
        page: int,
        limit: int,
        title: Optional[str],
        genre: Optional[str],
        language: Optional[str],
        release_year: Optional[int],
        sort_by: str,
        order: str,
        search_bar: bool = False,
    ):
        query = self._db.query(Movie)

        # ----- Search -----
        if title:
            # When title is provided, ignore all other filters
            pattern = f"%{title}%" if search_bar else f"{title}%"
            query = query.filter(
                Movie.title.ilike(pattern)
            )

        else:
            # ----- Genre Filter -----
            if genre:
                genres_list = [g.strip() for g in genre.split(",")]
                # Use OR logic for genres (match ANY of the selected genres)
                query = query.filter(
                    or_(*[Movie.genres.ilike(f"%{g}%") for g in genres_list])
                )

            # ----- Other Filters -----
            if language:
                # Language comes as comma-separated string, split it
                languages_list = [l.strip() for l in language.split(",")]
                query = query.filter(Movie.original_language.in_(languages_list))

            if release_year:
                query = query.filter(Movie.release_year == release_year)

        # ----- Sorting -----
        sort_map = {
            "popularity": Movie.popularity,
            "title": Movie.title,
            "release_year": Movie.release_year,
        }
        column = sort_map.get(sort_by, Movie.popularity)
        query = query.order_by(column.desc() if order == "desc" else column.asc())

        # ----- Count Total -----
        total = query.count()

        # ----- Pagination -----
        skip = (page - 1) * limit
        items = query.offset(skip).limit(limit).all()

        return [MovieResponse.model_validate(m) for m in items], total
