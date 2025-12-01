import numpy as np
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from tqdm import tqdm

# -------------------------
# CONFIG
# -------------------------
EMB_FILE = "data/movie_embeddings.npy"
META_FILE = "data/movie_metadata.parquet"

QDRANT_URL = "http://localhost:6333"
COLLECTION = "movies"

BATCH_SIZE = 500

# -------------------------
# LOAD DATA
# -------------------------
print("📥 Loading embeddings...")
embeddings = np.load(EMB_FILE)

print("📥 Loading metadata...")
df = pd.read_parquet(META_FILE)

dim = embeddings.shape[1]
print(f"📏 Embedding dimension: {dim}")
print(f"🎬 Total movies: {len(df)}")

# -------------------------
# CONNECT QDRANT
# -------------------------
print("🔌 Connecting to Qdrant...")
qdrant = QdrantClient(QDRANT_URL)

# Recreate collection
print("🆕 Creating collection...")
qdrant.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
)

# -------------------------
# INDEX
# -------------------------
print("🚀 Indexing into Qdrant...")

for i in tqdm(range(0, len(df), BATCH_SIZE)):
    batch = df.iloc[i:i + BATCH_SIZE]
    vectors = embeddings[batch["embedding_index"].values]

    points = [
        PointStruct(
            id=int(row["id"]),
            vector=vectors[j].tolist(),
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
        for j, (_, row) in enumerate(batch.iterrows())
    ]

    qdrant.upsert(
        collection_name=COLLECTION,
        points=points
    )

print("🎉 Done indexing saved embeddings into Qdrant!")
