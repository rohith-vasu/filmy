import pandas as pd
import numpy as np
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from tqdm import tqdm

# -----------------------------
# CONFIG
# -----------------------------
PARQUET_FILE = "data/tmdb_dataset_cleaned.parquet"

DB_USER = "filmy"
DB_PASS = "filmy"
DB_HOST = "localhost"
DB_NAME = "filmy_db"
DB_PORT = 5432

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

CHUNK_SIZE = 5000  # adjustable


# -----------------------------
# LOAD DF
# -----------------------------
print("📦 Loading parquet file...")
df = pd.read_parquet(PARQUET_FILE)

# rename id → tmdb_id
df.rename(columns={"id": "tmdb_id"}, inplace=True)

# replace NaN with None for Postgres
df = df.replace({np.nan: None})

columns = [
    "tmdb_id", "title", "overview", "genres", "original_language",
    "tagline", "keywords", "runtime", "popularity",
    "poster_path", "release_year"
]

df = df[columns]


# -----------------------------
# DB SETUP
# -----------------------------
engine = create_engine(DATABASE_URL)
meta = MetaData()
meta.reflect(bind=engine)
movies_table = meta.tables["movies"]

total_rows = len(df)
total_chunks = (total_rows // CHUNK_SIZE) + 1

print(f"🚀 Starting insert: {total_rows} rows, {total_chunks} chunks")


# -----------------------------
# INSERT WITH PROGRESS BAR
# -----------------------------
with engine.begin() as conn:
    for start in tqdm(range(0, total_rows, CHUNK_SIZE), desc="Inserting chunks", unit="chunk"):
        chunk_df = df.iloc[start:start + CHUNK_SIZE]
        records = chunk_df.to_dict(orient="records")

        stmt = insert(movies_table).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=["tmdb_id"])

        conn.execute(stmt)

print("✅ Done! All movies inserted into Postgres.")
