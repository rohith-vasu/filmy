import os
import sys
import random
import math
import time
import json
from collections import Counter, defaultdict
from faker import Faker
from tqdm import tqdm
from typing import List

# make import robust if running from repo root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.db import get_global_db_session
from app.model_handlers.user_handler import UserHandler, UserCreate
from app.model_handlers.user_feedback_handler import UserFeedbackHandler, UserFeedbackCreate
from app.model_handlers.movie_handler import MovieHandler

fake = Faker()

# Read config file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "generate_config.json")
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

# =========================
# CONFIG 
# =========================
TOTAL_USERS = CONFIG["TOTAL_USERS"]
ACTIVE_MOVIES = CONFIG["ACTIVE_MOVIES"]
CLUSTERS = CONFIG["CLUSTERS"]

# User interaction density (reduced for ALS sparsity)
AVG_INTERACTIONS = CONFIG["AVG_INTERACTIONS"]
MIN_INTERACTIONS = CONFIG["MIN_INTERACTIONS"]
MAX_INTERACTIONS = CONFIG["MAX_INTERACTIONS"]

# Popularity tiers — keep same
TIER_A = CONFIG["TIER_A"]
TIER_B = CONFIG["TIER_B"]
TIER_C = CONFIG["TIER_C"]
TIER_D = ACTIVE_MOVIES - (TIER_A + TIER_B + TIER_C)

# Cluster movie selection
CLUSTER_POOL_SIZE = CONFIG["CLUSTER_POOL_SIZE"]      
CLUSTER_POOL_OVERLAP = CONFIG["CLUSTER_POOL_OVERLAP"]

# Batch size
FEEDBACK_BATCH_SIZE = CONFIG["FEEDBACK_BATCH_SIZE"]

# Cluster vs random picks
FRACTION_CLUSTER_POOL = CONFIG["FRACTION_CLUSTER_POOL"]
FRACTION_POPULARITY = CONFIG["FRACTION_POPULARITY"]
FRACTION_TAIL = CONFIG["FRACTION_TAIL"]

RATING_CHOICES = CONFIG["RATING_CHOICES"]
RATING_WEIGHTS = CONFIG["RATING_WEIGHTS"]

# random seed
SEED = 42

# =========================
# HELPERS
# =========================
def random_password(length=12):
    return ''.join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(length))

def user_interactions_count(avg=AVG_INTERACTIONS):
    # smaller stddev so interactions are not extreme
    n = int(random.gauss(avg, avg * 0.25))
    return max(MIN_INTERACTIONS, min(MAX_INTERACTIONS, n))

def dedupe_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def make_feedback(user_id: int, movie_id: int, rating: float):
    return UserFeedbackCreate(user_id=user_id, movie_id=movie_id, rating=rating, status="watched")

def safe_bulk_create(feedback_handler: UserFeedbackHandler, objs: List[UserFeedbackCreate]):
    # prefer handler.bulk_create
    try:
        if hasattr(feedback_handler, "bulk_create"):
            feedback_handler.bulk_create(objs)
            return True, len(objs)
    except Exception as e:
        print("handler.bulk_create failed:", e)
        try:
            feedback_handler.db.rollback()
        except Exception:
            pass

    # fallback: bulk_save_objects if model available
    try:
        model_cls = getattr(feedback_handler, "_model", None)
        if model_cls is not None:
            db = feedback_handler.db
            rows = []
            for o in objs:
                if hasattr(o, "model_dump"):
                    rows.append(model_cls(**o.model_dump()))
                else:
                    # convert pydantic-like to dict safely
                    rows.append(model_cls(**(o.__dict__ if hasattr(o, "__dict__") else dict(o))))
            db.bulk_save_objects(rows)
            db.commit()
            return True, len(rows)
    except Exception as e:
        print("bulk_save_objects failed:", e)
        try:
            feedback_handler.db.rollback()
        except Exception:
            pass

    # last resort: insert one-by-one
    inserted = 0
    for o in objs:
        try:
            feedback_handler.create(o)
            inserted += 1
        except Exception:
            try:
                feedback_handler.db.rollback()
            except Exception:
                pass
            continue
    return True, inserted

# =========================
# MAIN
# =========================
def generate_v6():
    random.seed(SEED)
    t0 = time.time()
    print("🚀 Starting Synthetic Generator v6 — Improved signal")
    print(f"Target users: {TOTAL_USERS}, Active movies: {ACTIVE_MOVIES}, Clusters: {CLUSTERS}")

    db: Session = next(get_global_db_session())
    user_handler = UserHandler(db)
    feedback_handler = UserFeedbackHandler(db)
    movie_handler = MovieHandler(db)

    # load movies
    print("📥 Loading movies from DB (will pick active subset by popularity)...")
    all_movies = movie_handler.list_all(skip=0, limit=400000)
    if not all_movies:
        print("❌ No movies found. Aborting.")
        return

    # sort by popularity descending and pick candidate pool
    sorted_by_pop = sorted(all_movies, key=lambda m: float(m.popularity or 0.0), reverse=True)
    if len(sorted_by_pop) < ACTIVE_MOVIES:
        print(f"⚠️ Only {len(sorted_by_pop)} movies available; adjusting ACTIVE_MOVIES.")
        active_movies_list = sorted_by_pop
    else:
        candidate_cut = min(len(sorted_by_pop), int(ACTIVE_MOVIES * 1.2))
        candidates = sorted_by_pop[:candidate_cut]
        # sample weighted by popularity but keep top coverage
        pops = [max(0.001, float(m.popularity or 1.0)) for m in candidates]
        pow_pops = [p ** 1.2 for p in pops]
        s = sum(pow_pops)
        probs = [p / s for p in pow_pops]
        chosen_indices = set(random.choices(range(len(candidates)), weights=probs, k=ACTIVE_MOVIES))
        chosen = [candidates[i] for i in chosen_indices]
        # pad if needed (shouldn't)
        if len(chosen) < ACTIVE_MOVIES:
            chosen = candidates[:ACTIVE_MOVIES]
        active_movies_list = chosen[:ACTIVE_MOVIES]

    print(f"Active movie pool size: {len(active_movies_list)}")

    movie_by_id = {m.id: m for m in active_movies_list}
    active_ids = list(movie_by_id.keys())
    pops_active = [max(0.001, float(movie_by_id[mid].popularity or 1.0)) for mid in active_ids]
    pops_active = [p ** 1.2 for p in pops_active]
    s = sum(pops_active)
    pop_probs_active = [p / s for p in pops_active]
    id_to_index = {mid: i for i, mid in enumerate(active_ids)}

    # build tiers
    tier_a_ids = active_ids[:TIER_A]
    tier_b_ids = active_ids[TIER_A:TIER_A + TIER_B]
    tier_c_ids = active_ids[TIER_A + TIER_B:TIER_A + TIER_B + TIER_C]
    tier_d_ids = active_ids[TIER_A + TIER_B + TIER_C: ACTIVE_MOVIES]

    print(f"Tiers -> A:{len(tier_a_ids)}, B:{len(tier_b_ids)}, C:{len(tier_c_ids)}, D:{len(tier_d_ids)}")

    # ====================
    # Build cluster genre identities
    # ====================
    print("🔍 Extracting popular genres from active pool for cluster identities...")
    genre_counter = Counter()
    movie_genres_map = {}
    for m in active_movies_list:
        gs = m.genres or ""
        if isinstance(gs, str):
            g_list = [x.strip() for x in gs.split(",") if x.strip()]
        elif isinstance(gs, list):
            g_list = [str(x) for x in gs]
        else:
            g_list = []
        movie_genres_map[m.id] = g_list
        for g in g_list:
            genre_counter[g] += 1

    popular_genres = [g for g, _ in genre_counter.most_common()][:40]  # top genres to use
    if not popular_genres:
        # fallback small synthetic set
        popular_genres = ["Action", "Drama", "Comedy", "Romance", "Horror", "Documentary", "Sci-Fi", "Fantasy"]

    # produce cluster_genres: assign 2 distinct genres per cluster sampled from popular_genres
    random.shuffle(popular_genres)
    cluster_genres = {}
    for ci in range(CLUSTERS):
        a = popular_genres[ci % len(popular_genres)]
        b = popular_genres[(ci + 3) % len(popular_genres)]
        cluster_genres[ci] = list({a, b})

    print(f"Assigned cluster genres (sample): {dict(list(cluster_genres.items())[:5])}")

    # Build clusters with low overlap
    print("🔧 Building cluster pools with low overlap...")
    shuffled = active_ids[:]
    random.shuffle(shuffled)
    n = len(shuffled)
    pool_size = min(CLUSTER_POOL_SIZE, n)
    # step ensures overlap is small:
    step = max(1, int(pool_size * (1 - CLUSTER_POOL_OVERLAP)))
    clusters_info = []
    start = 0
    for ci in range(CLUSTERS):
        pool = []
        for i in range(pool_size):
            idx = (start + i) % n
            pool.append(shuffled[idx])
        start = (start + step) % n
        # filter pool to prefer movies that match cluster genres (increase genre coherence)
        # compute local popularity for pool
        pool_probs = [pop_probs_active[id_to_index[mid]] for mid in pool]
        s2 = sum(pool_probs) or 1.0
        pool_probs = [p / s2 for p in pool_probs]
        # boost weights for movies that match cluster genres
        boost = []
        cg = set(cluster_genres[ci])
        for i, mid in enumerate(pool):
            mg = set(movie_genres_map.get(mid, []))
            if mg & cg:
                pool_probs[i] *= 1.8  # boost matches
        # normalize again
        s3 = sum(pool_probs) or 1.0
        pool_probs = [p / s3 for p in pool_probs]
        clusters_info.append({"id": ci, "pool": pool, "pool_probs": pool_probs, "genres": cluster_genres[ci]})
    print(f"Built {len(clusters_info)} clusters.")

    # --------------- create users ---------------
    print("🧑‍💻 Creating users and assigning clusters...")
    users = []
    users_per_cluster = math.ceil(TOTAL_USERS / CLUSTERS)
    uid = 1
    for cidx, c in enumerate(tqdm(clusters_info, desc="Clusters")):
        # for each cluster create users_per_cluster users until total achieved
        for _ in range(users_per_cluster):
            if len(users) >= TOTAL_USERS:
                break
            try:
                email = f"{fake.user_name()}_{uid}_{random.randint(1000,9999)}@filmy.com"
                user = user_handler.create(UserCreate(
                    email=email,
                    firstname=fake.first_name(),
                    lastname=fake.last_name(),
                    hashed_password=random_password(),
                ))
                # assign genre preferences equal to cluster genres plus small random variation
                prefs = list(c["genres"])
                # occasionally add one extra preference
                if random.random() < 0.2:
                    prefs.append(random.choice(popular_genres))
                user.genre_preferences = ",".join(prefs)
                user_handler.update(user.id, user)
                users.append({"id": user.id, "cluster": cidx, "prefs": prefs})
                uid += 1
            except SQLAlchemyError as e:
                print("User creation error:", e)
                try:
                    user_handler.db.rollback()
                except Exception:
                    pass
                continue

    print(f"Created {len(users)} users.")

    # --------------- generate feedback ---------------
    print("🎯 Generating feedback per user (bulk)...")
    feedback_buffer = []
    total_feedback = 0
    errors = 0
    start_time = time.time()

    def pick_from_pool_with_probs(pool_list, pool_probs, k):
        if k <= 0:
            return []
        picks_idx = random.choices(range(len(pool_list)), weights=pool_probs, k=k)
        return [pool_list[i] for i in picks_idx]

    for u in tqdm(users, desc="Users -> Feedback"):
        user_id = u["id"]
        cluster_id = u["cluster"]
        prefs = u["prefs"]
        cinfo = clusters_info[cluster_id]
        pool_list = cinfo["pool"]
        pool_probs = cinfo["pool_probs"]

        n = user_interactions_count()
        k_cluster = int(round(n * FRACTION_CLUSTER_POOL))
        k_pop = int(round(n * FRACTION_POPULARITY))
        k_tail = n - (k_cluster + k_pop)

        chosen = []

        # 1) cluster pool preferential picks (genre biased)
        sample_for_rank = pool_list[:min(len(pool_list), 2000)]
        scored = []
        prefs_lower = [p.lower() for p in prefs]
        for mid in sample_for_rank:
            mg = movie_genres_map.get(mid, [])
            score = 0
            for g in mg:
                if g.lower() in prefs_lower:
                    score += 1
            scored.append((score, mid))
        scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
        pref_ids = [mid for _, mid in scored_sorted[:min(len(scored_sorted), max(50, int(k_cluster * 1.8)))]]  # a pool
        if pref_ids and len(pref_ids) >= k_cluster:
            # sample from top pref_ids but not always perfect: weight sampling by score
            chosen.extend(random.sample(pref_ids, k_cluster))
        else:
            chosen.extend(pick_from_pool_with_probs(pool_list, pool_probs, k_cluster))

        # 2) popularity sampling (small)
        pop_pool = []
        pop_weights = []
        if tier_a_ids:
            pop_pool.extend(tier_a_ids)
            pop_weights.extend([3.0] * len(tier_a_ids))
        if tier_b_ids:
            pop_pool.extend(tier_b_ids)
            pop_weights.extend([1.2] * len(tier_b_ids))
        if tier_c_ids:
            pop_pool.extend(tier_c_ids)
            pop_weights.extend([0.6] * len(tier_c_ids))
        if pop_pool and k_pop > 0:
            s_pop = sum(pop_weights)
            pop_probs = [w / s_pop for w in pop_weights]
            picks = random.choices(pop_pool, weights=pop_probs, k=k_pop)
            chosen.extend(picks)

        # 3) tail picks (tier D) - increase chance to choose items only in a single cluster
        if k_tail > 0 and len(tier_d_ids) > 0:
            tail_pick = random.sample(tier_d_ids, min(k_tail, len(tier_d_ids)))
            chosen.extend(tail_pick)

        # dedupe and top-up if needed
        final_ids = dedupe_keep_order(chosen)
        if len(final_ids) < n:
            need = n - len(final_ids)
            more = pick_from_pool_with_probs(pool_list, pool_probs, need * 2)
            for mid in more:
                if mid not in final_ids:
                    final_ids.append(mid)
                if len(final_ids) >= n:
                    break
        final_ids = final_ids[:n]

        # build feedback objects
        for mid in final_ids:
            rating = random.choices(RATING_CHOICES, weights=RATING_WEIGHTS, k=1)[0]
            feedback_buffer.append(make_feedback(user_id, mid, rating))
            total_feedback += 1

            if len(feedback_buffer) >= FEEDBACK_BATCH_SIZE:
                ok, inserted = safe_bulk_create(feedback_handler, feedback_buffer)
                if not ok:
                    errors += 1
                feedback_buffer.clear()

    # final flush
    if feedback_buffer:
        ok, inserted = safe_bulk_create(feedback_handler, feedback_buffer)
        if not ok:
            errors += 1
        feedback_buffer.clear()

    elapsed = time.time() - start_time
    print("\n🎉 Generation complete")
    print(f"Users created: {len(users)}")
    print(f"Total feedback rows inserted (approx): {total_feedback}")
    print(f"Errors: {errors}")
    print(f"Elapsed: {elapsed:.1f}s — ~{total_feedback/elapsed:.1f} inserts/sec")
    print(f"Script total time: {time.time() - t0:.1f}s")

if __name__ == "__main__":
    generate_v6()
