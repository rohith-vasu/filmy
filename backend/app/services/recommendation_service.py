from typing import List, Optional
from sqlalchemy.orm import Session
import numpy as np
import os
import pickle

from app.core.qdrant import get_qdrant_client
from app.model_handlers.movie_handler import MovieHandler
from app.model_handlers.user_handler import UserHandler
from app.model_handlers.user_feedback_handler import UserFeedbackHandler
from app.utils.model_loader import load_latest_production_model

from app.model_state import MODEL_CACHE

from loguru import logger

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.movie_handler = MovieHandler(db)
        self.user_handler = UserHandler(db)
        self.feedback_handler = UserFeedbackHandler(db)
        self.qdrant = get_qdrant_client()

        # load model artifacts from MODEL_CACHE (populated by loader)
        self.implicit_model = MODEL_CACHE.get("implicit_model")
        self.dataset_map = MODEL_CACHE.get("dataset_map")
        self.item_factors = MODEL_CACHE.get("item_factors")
        self.user_factors = MODEL_CACHE.get("user_factors")

    def _rerank_with_implicit(self, user_id: int, candidate_ids: List[int]) -> List[int]:
        """
        Rerank candidate ids using ALS user/item factors.
        Under A1, item_factors and user_factors are available for full catalog.
        """
        if not self.implicit_model or not self.dataset_map:
            return candidate_ids

        user_map = self.dataset_map["user_map"]
        item_map = self.dataset_map["item_map"]

        # if user not in map, cannot use ALS re-rank
        if user_id not in user_map:
            return candidate_ids

        uidx = user_map[user_id]
        user_vec = self.user_factors[uidx] if self.user_factors is not None else self.implicit_model.user_factors[uidx]

        # Map candidates to indices where possible. Because A1 maps all items, we expect all candidates present.
        indices = []
        mapped = []
        for cid in candidate_ids:
            if cid in item_map:
                indices.append(item_map[cid])
                mapped.append(cid)
            else:
                # If some item is missing (unlikely in A1), we keep it for fallback scoring
                mapped.append(cid)

        if not indices:
            return candidate_ids

        item_vecs = self.item_factors[indices]
        scores = item_vecs.dot(user_vec)
        order = np.argsort(-scores)
        ordered = [mapped[i] for i in order]
        # There may be candidate ids not mapped (if any); append them at the end
        unmapped = [cid for cid in candidate_ids if cid not in ordered]
        return ordered + unmapped

    def recommend_for_cold_start(self, user_id: int, limit: int = 10):
        user = self.user_handler.get_by_id(user_id)
        if not user or not user.genre_preferences:
            popular = self.movie_handler.list_all(skip=0, limit=limit*3)
            return [self.movie_handler._response_schema.model_validate(m) for m in popular[:limit]]

        genres = [g.strip() for g in user.genre_preferences.split(",") if g.strip()]
        if not genres:
            popular = self.movie_handler.list_all(skip=0, limit=limit*3)
            return [self.movie_handler._response_schema.model_validate(m) for m in popular[:limit]]

        query = f"Movies in genres: {', '.join(genres)}. Recommend good movies."
        vec = self.qdrant.embedding_model.encode(query, normalize_embeddings=True).tolist()
        results = self.qdrant.search_similar(movie_vector=vec, top=limit * 50)
        filtered = []
        for r in results:
            movie = self.movie_handler.get_by_id(int(r["id"]))
            if movie and any(g.lower() in (movie.genres or "").lower() for g in genres):
                filtered.append(movie)
        filtered = sorted(filtered, key=lambda m: m.popularity or 0, reverse=True)
        return [self.movie_handler._response_schema.model_validate(m) for m in filtered[:limit]]

    def guest_recommendations(
        self, 
        genres: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        limit: int = 10
    ):
        if examples:
            docs = []
            movie_ids = []
            for ex in examples:
                movie = self.movie_handler.get_by_title(ex)
                if movie:
                    movie_ids.append(movie.id)
                    movie_text = f"""
                        Title: {movie.title}
                        Overview: {movie.overview}
                        Genres: {movie.genres}
                        Tagline: {movie.tagline}
                        Keywords: {movie.keywords}
                        Language: {movie.original_language}
                    """.strip()
                    docs.append(movie_text)
                else:
                    docs.append(ex)
            query = " ".join(docs)
            vec = self.qdrant.embedding_model.encode(query, normalize_embeddings=True).tolist()
            qres = self.qdrant.search_similar(movie_vector=vec, top=limit * 2)
            candidate_ids = [int(r["id"]) for r in qres if int(r["id"]) not in movie_ids]
            movies = [self.movie_handler.get_by_id(id) for id in candidate_ids]
            # keep order and remove Nones
            ordered = [m for m in (movies) if m]
            return ordered[:limit]

        if genres:
            return self.movie_handler.get_by_genres(genres, limit=limit)

        # fallback: popular
        return self.movie_handler.list_all(skip=0, limit=limit)


    def personalized_recommendations(self, user_id: int, limit: int = 10):
        feedbacks = self.feedback_handler.get_user_feedbacks(user_id)
        if not feedbacks:
            return self.recommend_for_cold_start(user_id, limit)

        if not self.implicit_model or not self.dataset_map:
            return self.recommend_for_cold_start(user_id, limit)

        user_map = self.dataset_map.get("user_map", {})
        item_map = self.dataset_map.get("item_map", {})

        if user_id not in user_map:
            return self.recommend_for_cold_start(user_id, limit)

        model_user_index = user_map[user_id]

        # Candidate generation using recent watched
        recent = feedbacks[-10:]
        movie_ids = [f.movie_id for f in recent]
        texts = []
        for mid in movie_ids:
            m = self.movie_handler.get_by_id(mid)
            if m:
                texts.append(f"{m.title}. {m.overview or ''}. Genres: {m.genres or ''}")
        query = " ".join(texts) if texts else None

        candidate_ids = []
        if query:
            vec = self.qdrant.embedding_model.encode(query, normalize_embeddings=True).tolist()
            # fetch a much larger pool to give ALS room to rerank
            qres = self.qdrant.search_similar(movie_vector=vec, top=limit * 200)
            candidate_ids = [int(r["id"]) for r in qres]
        else:
            candidate_rows = self.movie_handler.list_all(skip=0, limit=limit * 200)
            candidate_ids = [m.id for m in candidate_rows]

        if not candidate_ids:
            return self.recommend_for_cold_start(user_id, limit)

        # Rerank candidates with ALS (A1: item_factors available for full catalog)
        ranked_candidate_ids = self._rerank_with_implicit(user_id, candidate_ids)

        # Filter watched: only remove movies the user has actually watched (lifetime)
        watched = {fb.movie_id for fb in feedbacks}
        final_ids = [mid for mid in ranked_candidate_ids if mid not in watched]

        # If not enough after filtering, fill with popularity-based items not watched
        if len(final_ids) < limit:
            need = limit - len(final_ids)
            popular_rows = self.movie_handler.list_all(skip=0, limit=limit * 50)
            popular_ids = [m.id for m in popular_rows if m.id not in watched and m.id not in final_ids]
            final_ids.extend(popular_ids[:need])

        final_ids = final_ids[:limit]

        movies = [self.movie_handler.get_by_id(mid) for mid in final_ids]
        return [self.movie_handler._response_schema.model_validate(m) for m in movies if m]

    def recommendations_based_on_recent_activity(
        self,
        user_id: int,
        limit: int = 12,
        last_n: int = 3
    ):
        fb_q = (
            self.db.query(self.feedback_handler._model)
            .filter(self.feedback_handler._model.user_id == user_id, self.feedback_handler._model.status == "watched")
            .order_by(self.feedback_handler._model.created_at.desc())
            .limit(last_n)
            .all()
        )
        if not fb_q:
            return []

        candidate_scores = {}
        for fb in fb_q:
            movie = self.movie_handler.get_by_id(fb.movie_id)
            if not movie: 
                continue
            movie_text = f"""
                    Title: {movie.title}
                    Overview: {movie.overview}
                    Genres: {movie.genres}
                    Tagline: {movie.tagline}
                    Keywords: {movie.keywords}
                    Language: {movie.original_language}
                """.strip()
            vec = self.qdrant.embedding_model.encode(movie_text, normalize_embeddings=True).tolist()
            qres = self.qdrant.search_similar(movie_vector=vec, top=limit*2)
            for r in qres:
                mid = int(r["id"])
                candidate_scores[mid] = max(candidate_scores.get(mid, 0.0), r["score"])

        # remove watched
        watched = {fb.movie_id for fb in self.feedback_handler.get_user_feedbacks(user_id)}
        candidates = [(mid, score) for mid, score in candidate_scores.items() if mid not in watched]
        top = sorted(candidates, key=lambda x: -x[1])[:limit]
        movies = [self.movie_handler.get_by_id(mid) for mid, _ in top]
        return [self.movie_handler._response_schema.model_validate(m) for m in movies if m]


    def search_recommendations(
        self,
        user_id: Optional[int],
        query_movies: Optional[List[str]],
        genres: Optional[List[str]],
        languages: Optional[List[str]],
        year_min: Optional[int],
        year_max: Optional[int],
        limit: int = 20,
    ):
        # Build Qdrant filter
        q_filters = {}

        if genres:
            q_filters["genres"] = genres

        if languages:
            q_filters["original_language"] = languages

        if year_min or year_max:
            q_filters["release_year"] = {
                "gte": year_min,
                "lte": year_max
            }

        # Similarity Mode
        if query_movies:
            examples_res = self.guest_recommendations(examples=query_movies, limit=limit * 40)
            raw_results = [{"id": m.id, "score": getattr(m, "popularity", 0)} for m in examples_res]

        # Filter Mode
        else:
            query = "movies recommended to watch"
            vector = self.qdrant.embedding_model.encode(query, normalize_embeddings=True).tolist()

            raw_results = self.qdrant.search_similar(
                movie_vector=vector,
                top=limit * 40,
                filters=q_filters
            )

        candidate_ids = [r["id"] for r in raw_results]

        # Personalized re-ranking (ALS)
        if user_id and self.implicit_model:
            ranked_ids = self._rerank_with_implicit(user_id, candidate_ids)
        else:
            ranked_ids = candidate_ids

        # Remove watched movies
        if user_id:
            watched = {f.movie_id for f in self.feedback_handler.get_user_feedbacks(user_id)}
            ranked_ids = [mid for mid in ranked_ids if mid not in watched]

        # Build final movie responses
        movies = [self.movie_handler.get_by_id(mid) for mid in ranked_ids[:limit]]
        return [self.movie_handler._response_schema.model_validate(m) for m in movies if m]
        

    def similar_movies(self, movie_id: int, limit: int = 10):
        # Get the movie by ID
        movie = self.movie_handler.get_by_id(movie_id)
        if not movie:
            return []
        
        # Create a text representation of the movie for embedding
        movie_text = f"""
                Title: {movie.title}
                Overview: {movie.overview}
                Genres: {movie.genres}
                Tagline: {movie.tagline}
                Keywords: {movie.keywords}
                Language: {movie.original_language}
            """.strip()
        
        # Create vector from the movie text
        vec = self.qdrant.embedding_model.encode(movie_text, normalize_embeddings=True).tolist()
        
        # Search for similar movies (get extra to account for filtering)
        qres = self.qdrant.search_similar(movie_vector=vec, top=limit + 10)
        
        # Filter out the input movie and get movie objects
        candidate_ids = [int(r["id"]) for r in qres if int(r["id"]) != movie_id]
        movies = [self.movie_handler.get_by_id(id) for id in candidate_ids]
        
        # Remove None values and convert to response schema
        valid_movies = [m for m in (movies) if m]
        
        return valid_movies[:limit]
