from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from loguru import logger
from typing import List, Dict, Optional
import numpy as np
from app.core.settings import settings


class Qdrant:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant.url,
        )

        # Sentence-transformer for movie embeddings
        self.embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        self.collection_name = settings.qdrant.collection

        # Ensure the collection exists
        self._ensure_collection()

    # --------------------------
    # Collection Management
    # --------------------------
    def _ensure_collection(self):
        """Ensure the Qdrant collection for movies exists and has correct config."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            if collection_info.config.params.vectors.size != 768:
                logger.warning(f"⚠️ Collection '{self.collection_name}' has incorrect vector size. Recreating...")
                self.client.delete_collection(self.collection_name)
                raise Exception("Collection deleted due to config mismatch")
            
            logger.info(f"✅ Qdrant collection '{self.collection_name}' exists with correct config.")
        except Exception:
            logger.info(f"⚙️ Creating Qdrant collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
                on_disk_payload=True,
            )

    # --------------------------
    # Embedding Helper
    # --------------------------
    def _build_movie_embedding(self, title: str, overview: str, genres: List[str]) -> np.ndarray:
        """Generate a dense embedding for a movie."""
        text = f"{title}. {overview or ''}. Genres: {', '.join(genres or [])}."
        return self.embedding_model.encode(text, normalize_embeddings=True)

    # --------------------------
    # CRUD Operations
    # --------------------------
    def upsert_movies(self, movies: List[Dict]):
        """
        Upsert multiple movie vectors into Qdrant.
        Each movie dict should include:
        {
            "id": int,
            "title": str,
            "overview": str,
            "genres": list[str],
            "release_year": int,
            "popularity": float
        }
        """
        if not movies:
            logger.warning("⚠️ No movies to upsert into Qdrant.")
            return

        logger.info(f"🚀 Upserting {len(movies)} movies into Qdrant...")

        vectors = []
        payloads = []

        for m in movies:
            vector = self._build_movie_embedding(m["title"], m.get("overview", ""), m.get("genres", []))
            vectors.append(vector)
            payloads.append({
                "id": m["id"],
                "title": m["title"],
                "genres": m.get("genres", []),
                "release_year": m.get("release_year"),
                "popularity": m.get("popularity"),
            })

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(id=m["id"], vector=vectors[i], payload=payloads[i])
                for i, m in enumerate(movies)
            ],
        )

        logger.info(f"✅ Upserted {len(movies)} movies to Qdrant.")

    def delete_movie(self, movie_id: int):
        """Delete a single movie vector from Qdrant."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[movie_id]),
        )
        logger.info(f"🗑️ Deleted movie {movie_id} from Qdrant.")

    def clear_collection(self):
        """Delete all movie vectors (use carefully)."""
        self.client.delete_collection(self.collection_name)
        logger.warning(f"⚠️ Collection '{self.collection_name}' deleted.")

    # --------------------------
    # Search Operations
    # --------------------------
    def search_similar(
        self,
        query: Optional[str] = None,
        movie_vector: Optional[np.ndarray] = None,
        top: int = 10,
        filters: Optional[Dict] = None,
    ):
        if query:
            vector = self.embedding_model.encode(query, normalize_embeddings=True)
        elif movie_vector is not None:
            vector = movie_vector
        else:
            raise ValueError("Either query or movie_vector must be provided.")

        qdrant_filter = None
        if filters:
            must = []

            for key, val in filters.items():

                # LIST MATCH (genres, language)
                if isinstance(val, list):
                    must.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=val)
                        )
                    )

                # RANGE MATCH (release_year)
                elif isinstance(val, dict) and ("gte" in val or "lte" in val):
                    must.append(
                        models.FieldCondition(
                            key=key,
                            range=models.Range(
                                gte=val.get("gte"),
                                lte=val.get("lte"),
                            )
                        )
                    )

                # EXACT MATCH
                else:
                    must.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=val)
                        )
                    )

            qdrant_filter = models.Filter(must=must)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=qdrant_filter,
            limit=top,
        )

        return [
            {
                "id": r.payload["id"],
                "title": r.payload["title"],
                "genres": r.payload.get("genres"),
                "release_year": r.payload.get("release_year"),
                "language": r.payload.get("language"),
                "poster_path": r.payload.get("poster_path"),
                "popularity": r.payload.get("popularity"),
                "score": r.score,
            }
            for r in results
        ]



# -----------------------------
# ✅ Singleton instance helper
# -----------------------------
_qdrant_instance: Optional[Qdrant] = None

def get_qdrant_client() -> Qdrant:
    """Lazily initialize and return a global Qdrant instance."""
    global _qdrant_instance
    if _qdrant_instance is None:
        _qdrant_instance = Qdrant()
        logger.info("✅ Initialized global Qdrant client.")
    return _qdrant_instance
