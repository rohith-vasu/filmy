import os
import time
import requests
from app.core.settings import settings

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = settings.tmdb.base_url
TMDB_SLEEP = float(os.getenv("TMDB_SLEEP", 0.25))

def tmdb_get(path, params=None):
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    resp = requests.get(f"{TMDB_BASE}{path}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

def discover_new_movie_ids(from_date: str):
    page = 1
    ids = []

    while True:
        data = tmdb_get(
            "/discover/movie",
            {
                "primary_release_date.gte": from_date,
                "sort_by": "primary_release_date.asc",
                "page": page,
            }
        )

        ids.extend([m["id"] for m in data.get("results", [])])

        if page >= data.get("total_pages", 1):
            break

        page += 1

    return ids

def fetch_movie(movie_id: int):
    time.sleep(TMDB_SLEEP)
    return tmdb_get(f"/movie/{movie_id}", params={"append_to_response": "keywords"})
