import os
import time
import logging
from datetime import datetime, timedelta
from loguru import logger

import pandas as pd
import psycopg2
import psycopg2.extras

from app.pipelines.utils.storage import (
    get_s3fs,
    write_obj_to_minio,
    read_json_from_minio,
    upload_local_file_to_minio,
    dvc_config_remote,
    dvc_add_and_push,
)

from app.pipelines.utils.tmdb_client import (
    discover_new_movie_ids,
    fetch_movie,
)

from app.core.settings import settings
from app.pipelines.utils.index_embeddings import embed_and_index


BUCKET = os.getenv("MINIO_DATA_BUCKET", "filmy-data")
MASTER_KEY = "cleaned/tmdb_dataset_cleaned.parquet"
S3_ROOT = f"s3://{BUCKET}"
MASTER_PATH = f"{S3_ROOT}/{MASTER_KEY}"

username = settings.db.username
password = settings.DB_PASSWORD
host = settings.db.host
port = settings.db.port
database = settings.db.database

POSTGRES_DSN = f"postgresql://{username}:{password}@{host}:{port}/{database}"

# ----------------------------------------
# Major movie languages
# ----------------------------------------
LANGUAGE_MAP = {
    "en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil",
    "ml": "Malayalam", "kn": "Kannada", "bn": "Bengali", "mr": "Marathi",
    "or": "Oriya",
    "fr": "French", "de": "German", "it": "Italian", "es": "Spanish",
    "pt": "Portuguese", "nl": "Dutch", "sv": "Swedish", "da": "Danish",
    "fi": "Finnish", "pl": "Polish", "cs": "Czech", "sk": "Slovak",
    "sl": "Slovenian", "hr": "Croatian", "et": "Estonian", "lv": "Latvian"
}


# ----------------------------------------
# Backend data storage path
# ----------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_DIR = os.path.join(BASE_DIR, "backend", "data")
os.makedirs(DATA_DIR, exist_ok=True)

TMP_LOCAL = os.path.join(DATA_DIR, "master_ingest.parquet")
TMP_LOCAL_DVC = os.path.join(DATA_DIR, "master_for_dvc.parquet")


# ----------------------------------------
# Normalize TMDB data
# ----------------------------------------
def normalize_movie(m: dict) -> dict:
    genres = ",".join([g["name"] for g in m.get("genres", [])]) if m.get("genres") else None

    keywords = None
    try:
        kwlist = m.get("keywords", {}).get("keywords", [])
        keywords = ",".join([k["name"] for k in kwlist])
    except:
        pass

    lang_full = LANGUAGE_MAP.get(m.get("original_language"), m.get("original_language"))

    return {
        "tmdb_id": m.get("id"),
        "title": m.get("title"),
        "overview": m.get("overview") if m.get("overview") else "",
        "genres": genres,
        "original_language": lang_full,
        "tagline": m.get("tagline") if m.get("tagline") else "",
        "keywords": kw,
        "runtime": m.get("runtime") if m.get("runtime") else 0,
        "popularity": m.get("popularity") if m.get("popularity") else 0,
        "poster_path": m.get("poster_path") if m.get("poster_path") else "",
        "release_year": int(m["release_date"][:4]) if m.get("release_date") else None,
    }


# ----------------------------------------
# Database Upsert
# ----------------------------------------
def upsert_into_postgres(df: pd.DataFrame):
    if df.empty:
        logger.info("No rows to upsert into Postgres.")
        return pd.DataFrame()

    cols = list(df.columns)
    col_sql = ",".join([f'"{c}"' for c in cols])
    update_sql = ",".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != "tmdb_id"])

    insert_sql = f"""
        INSERT INTO movies ({col_sql})
        VALUES %s
        ON CONFLICT (tmdb_id)
        DO UPDATE SET {update_sql}
        RETURNING id, tmdb_id;
    """

    records = df.to_dict(orient="records")

    conn = psycopg2.connect(POSTGRES_DSN)
    try:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, insert_sql, records, page_size=500)
            result = cur.fetchall()     # list of (id, tmdb_id)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.exception("Upsert failed: %s", e)
        return pd.DataFrame()
    finally:
        conn.close()

    # convert to dataframe
    return pd.DataFrame(result, columns=["id", "tmdb_id"])


# ----------------------------------------
# Fetch movies by tmdb_ids
# ----------------------------------------
def fetch_movies_by_tmdb_ids(tmdb_ids):
    if not tmdb_ids:
        return pd.DataFrame()

    conn = psycopg2.connect(POSTGRES_DSN)
    df = pd.read_sql(
        """
        SELECT id, tmdb_id, title, overview, genres, original_language,
               tagline, keywords, runtime, popularity, release_year
        FROM movies
        WHERE tmdb_id = ANY(%s)
        ORDER BY id ASC
        """,
        conn,
        params=[list(tmdb_ids)]
    )
    conn.close()
    return df


# ----------------------------------------
# MAIN INGEST PIPELINE
# ----------------------------------------
def run_daily_ingest():

    fs = get_s3fs()

    # Load last ingest date
    meta = read_json_from_minio("metadata/last_ingest.json")
    last_ingest = meta["last_ingest"] if meta else (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Fetching movies since {last_ingest}")

    # 1. Discover new movies
    movie_ids = discover_new_movie_ids("2025-11-20")

    rows = []
    for mid in movie_ids:
        try:
            m = fetch_movie(mid)

            lang = m.get("original_language", "").lower()

            # Filters: released, not adult, allowed languages
            if m.get("status") != "Released":
                continue
            if m.get("adult") is True:
                continue
            if lang not in LANGUAGE_MAP:
                continue
            if m.get("title") == "":
                continue
            if m.get("release_date") == "":
                continue

            rows.append(normalize_movie(m))

        except Exception as e:
            logger.error(f"Error fetching movie {mid}: {e}")

    df_new = pd.DataFrame(rows)
    logger.info(f"{len(df_new)} new movies after filtering")

    # 2. Load master
    if fs.exists(MASTER_PATH):
        with fs.open(MASTER_PATH, "rb") as f:
            df_old = pd.read_parquet(f)
    else:
        df_old = pd.DataFrame()

    # 3. Merge + dedupe
    df_all = pd.concat([df_old, df_new], ignore_index=True)
    df_all = df_all.drop_duplicates(subset=["tmdb_id"], keep="last")

    # 4. Write new master parquet locally
    df_all.to_parquet(TMP_LOCAL, index=False)
    upload_local_file_to_minio(TMP_LOCAL, MASTER_KEY, bucket=BUCKET)
    logger.info("Uploaded updated master to MinIO")

    # Delete local file after upload
    if os.path.exists(TMP_LOCAL):
        os.remove(TMP_LOCAL)

    # 5. DVC tracking
    try:
        fs.get(MASTER_PATH, TMP_LOCAL_DVC)

        dvc_config_remote()
        dvc_add_and_push(TMP_LOCAL_DVC)

        # clean tmp file
        os.remove(TMP_LOCAL_DVC)

        logger.info("DVC updated with new dataset version")
    except Exception as e:
        logger.error(f"DVC update failed: {e}")

    # 6. Upsert new movies into Postgres → returns IDs
    df_upserted = upsert_into_postgres(df_new)

    # df_upserted contains: id, tmdb_id
    tmdb_ids = df_upserted["tmdb_id"].tolist()

    # 7. Fetch full movie rows including DB IDs
    df_final_new = fetch_movies_by_tmdb_ids(tmdb_ids)

    # 8. Embed + index to Qdrant
    embed_and_index(df_final_new)

    # 9. Update metadata
    write_obj_to_minio({"last_ingest": today}, "metadata/last_ingest.json")

    return {
        "new_movies": len(df_new),
        "total_master_rows": len(df_all),
        "last_ingest": today,
    }


if __name__ == "__main__":
    result = run_daily_ingest()
    logger.info(f"Ingest completed: {result}")
