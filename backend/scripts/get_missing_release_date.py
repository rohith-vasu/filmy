import asyncio
import aiohttp
import json
import os
from aiohttp import ClientSession, TCPConnector

API_KEY = "4aa15aa20fb2f87336706f86459a1bbe"
TMDB_URL = f"https://api.themoviedb.org/3/movie/{{}}?api_key={API_KEY}"

IDS_FILE = "missing_release_ids.json"
CHECKPOINT_FILE = "missing_release_dates.json"

BATCH_SIZE = 500
RATE_LIMIT = 10  # TMDB allows 10 req/sec

semaphore = asyncio.Semaphore(RATE_LIMIT)


# ------------------------------------------------
# Load the list of IDs to fetch
# ------------------------------------------------
with open(IDS_FILE, "r") as f:
    all_ids = json.load(f)

# Load or create checkpoint file
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r") as f:
        saved = json.load(f)
else:
    saved = {}

saved_ids = set(map(int, saved.keys()))
ids_to_fetch = [mid for mid in all_ids if mid not in saved_ids]

print(f"Total missing IDs: {len(all_ids)}")
print(f"Already processed: {len(saved_ids)}")
print(f"Remaining to fetch: {len(ids_to_fetch)}")


# ------------------------------------------------
# Fetch a single movie release date
# ------------------------------------------------
async def fetch_release_date(session, movie_id):
    async with semaphore:
        url = TMDB_URL.format(movie_id)
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return movie_id, data.get("release_date")
                return movie_id, None
        except:
            return movie_id, None


# ------------------------------------------------
# Save checkpoint
# ------------------------------------------------
def save_checkpoint(data):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("Saved checkpoint ✔")


# ------------------------------------------------
# Main async fetcher
# ------------------------------------------------
async def fetch_all(ids):
    connector = TCPConnector(limit=50)

    async with ClientSession(connector=connector) as session:
        tasks = []
        results = {}

        for i, movie_id in enumerate(ids):
            tasks.append(fetch_release_date(session, movie_id))

            # batch process
            if len(tasks) >= BATCH_SIZE:
                batch = await asyncio.gather(*tasks)
                tasks = []

                for mid, rdate in batch:
                    results[mid] = rdate
                    saved[str(mid)] = rdate

                save_checkpoint(saved)
                print(f"Processed {i + 1}/{len(ids)}")

                await asyncio.sleep(1)  # stable timing

        # final leftover batch
        if tasks:
            batch = await asyncio.gather(*tasks)
            for mid, rdate in batch:
                results[mid] = rdate
                saved[str(mid)] = rdate

            save_checkpoint(saved)

        return results


# ------------------------------------------------
# RUN
# ------------------------------------------------
results = asyncio.run(fetch_all(ids_to_fetch))

print("Completed fetching.")
print("Total saved:", len(saved))
