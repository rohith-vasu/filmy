import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import os

# -------------------------
# CONFIG
# -------------------------
DB_URL = "postgresql://filmy:filmy@localhost:5432/filmy_db"

OUTPUT_EMB = "data/movie_embeddings.npy"
OUTPUT_META = "data/movie_metadata.parquet"

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
BATCH_SIZE = 1000


# -------------------------
# LOAD MODEL
# -------------------------
print("🤖 Loading model...")
model = SentenceTransformer(MODEL_NAME)


# -------------------------
# LOAD MOVIES FROM DB
# -------------------------
print("🗄 Fetching movies...")
engine = create_engine(DB_URL)

df = pd.read_sql("""
    SELECT id, tmdb_id, title, overview, genres, original_language,
           tagline, keywords, runtime, popularity,
           release_year
    FROM movies
    ORDER BY id ASC
""", engine)

df = df.replace({np.nan: None})

print(f"🎬 Total movies: {len(df)}")


# -------------------------
# BUILD EMBEDDING TEXT
# -------------------------
def build_text(row):
    return f"""
Title: {row['title']}
Overview: {row['overview']}
Genres: {row['genres']}
Tagline: {row['tagline']}
Keywords: {row['keywords']}
Language: {row['original_language']}
""".strip()


# -------------------------
# EMBED MOVIES
# -------------------------
print("🔧 Generating embeddings...")

all_vectors = []
texts = [build_text(row) for _, row in df.iterrows()]

for i in tqdm(range(0, len(texts), BATCH_SIZE)):
    batch = texts[i:i + BATCH_SIZE]
    vectors = model.encode(batch, show_progress_bar=False)
    all_vectors.append(vectors)

embeddings = np.vstack(all_vectors)

print(f"✅ Embeddings generated: {embeddings.shape}")


# -------------------------
# SAVE TO DISK
# -------------------------
print("💾 Saving embeddings + metadata...")

df["embedding_index"] = range(len(df))  # ensure index alignment

np.save(OUTPUT_EMB, embeddings)
df.to_parquet(OUTPUT_META, index=False)

print(f"📁 Saved: {OUTPUT_EMB}")
print(f"📁 Saved: {OUTPUT_META}")
print("🎉 Done generating + saving embeddings.")
