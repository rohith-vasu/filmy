from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd


# Load once globally for speed
EMBED_MODEL = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "movies"


def build_text(row):
    return f"""
Title: {row['title']}
Overview: {row['overview']}
Genres: {row['genres']}
Tagline: {row['tagline']}
Keywords: {row['keywords']}
Language: {row['original_language']}
""".strip()


def embed_and_index(df_new: pd.DataFrame):
    if df_new.empty:
        logger.info("No new movies to embed/index.")
        return

    logger.info(f"Embedding + indexing {len(df_new)} new movies into Qdrant...")

    qdrant = QdrantClient(QDRANT_URL)

    # Ensure collection exists
    existing = qdrant.get_collections()
    if QDRANT_COLLECTION not in {c.name for c in existing.collections}:
        vec_dim = len(EMBED_MODEL.encode("hello world"))
        qdrant.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vec_dim, distance=Distance.COSINE),
        )

    # Embed
    texts = [build_text(row) for _, row in df_new.iterrows()]
    vectors = EMBED_MODEL.encode(texts, show_progress_bar=True)

    # Prepare points
    points = []
    for i, (_, row) in enumerate(df_new.iterrows()):
        points.append(
            PointStruct(
                id=int(row["id"]),
                vector=vectors[i].tolist(),
                payload={
                    "id": int(row["id"]),
                    "tmdb_id": int(row["tmdb_id"]),
                    "title": row["title"],
                    "overview": row["overview"],
                    "genres": row["genres"],
                    "release_year": row["release_year"],
                    "original_language": row["original_language"],
                    "popularity": row["popularity"],
                }
            )
        )

    qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
    logger.info(f"Indexed {len(points)} new movies into Qdrant.")