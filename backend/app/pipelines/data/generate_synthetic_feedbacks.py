#!/usr/bin/env python3
"""
Synthetic feedback generator (ALS-optimized):
- TOTAL_USERS users (includes fixed first user)
- ACTIVE_MOVIES selected by popularity for generation (ALS will be trained on full DB separately)
- First user (id created first): strict prefs ["Action","Mystery","Science Fiction","Thriller","Crime"]
  -> all interactions for this user are restricted to those genres (strict).
- Other users: 4-6 genres (min 4). Interactions biased to prefs (70%) + popularity (15%) + tail (15%).
- Sampling without replacement. Avoid inserting duplicate (user_id, movie_id).
- Robust bulk insert with fallbacks to avoid SQL unique constraint errors.
"""

import os
import sys
import json
import random
import math
import time
from collections import Counter
from typing import List

from faker import Faker
from tqdm import tqdm

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# robust repo import
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.core.db import get_global_db_session
from app.services.auth_service import AuthService
from app.model_handlers.user_handler import UserHandler, UserCreate
from app.model_handlers.user_feedback_handler import UserFeedbackHandler, UserFeedbackCreate
from app.model_handlers.movie_handler import MovieHandler

fake = Faker()

# Official genres
GENRES = [
    "Action","Adventure","Animation","Comedy","Crime","Documentary","Drama",
    "Family","Fantasy","History","Horror","Music","Mystery","Romance",
    "Science Fiction","TV Movie","Thriller","War","Western"
]

# Load config
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "generate_config.json")
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"{CONFIG_PATH} not found. Provide generate_config.json in the script folder.")
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)
CONFIG.setdefault("SEED", 42)

TOTAL_USERS = CONFIG["TOTAL_USERS"]
ACTIVE_MOVIES = CONFIG["ACTIVE_MOVIES"]
CLUSTERS = CONFIG["CLUSTERS"]

AVG_INTERACTIONS = CONFIG["AVG_INTERACTIONS"]
MIN_INTERACTIONS = CONFIG["MIN_INTERACTIONS"]
MAX_INTERACTIONS = CONFIG["MAX_INTERACTIONS"]

TIER_A = CONFIG["TIER_A"]
TIER_B = CONFIG["TIER_B"]
TIER_C = CONFIG["TIER_C"]
TIER_D = ACTIVE_MOVIES - (TIER_A + TIER_B + TIER_C)

CLUSTER_POOL_SIZE = CONFIG["CLUSTER_POOL_SIZE"]
CLUSTER_POOL_OVERLAP = CONFIG["CLUSTER_POOL_OVERLAP"]

FEEDBACK_BATCH_SIZE = CONFIG["FEEDBACK_BATCH_SIZE"]

FRACTION_CLUSTER_POOL = CONFIG["FRACTION_CLUSTER_POOL"]
FRACTION_POPULARITY = CONFIG["FRACTION_POPULARITY"]
FRACTION_TAIL = CONFIG["FRACTION_TAIL"]

RATING_CHOICES = CONFIG["RATING_CHOICES"]
RATING_WEIGHTS = CONFIG["RATING_WEIGHTS"]

SEED = CONFIG.get("SEED", 42)

MIN_USER_GENRES = 4
MAX_USER_GENRES = 6

# First user fixed preferences (strict)
FIRST_USER_PREFS = ["Action", "Mystery", "Science Fiction", "Thriller", "Crime"]

# Helpers
def random_password(length=12):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choice(chars) for _ in range(length))

def user_interactions_count():
    n = int(random.gauss(AVG_INTERACTIONS, AVG_INTERACTIONS * 0.20))
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
    """
    Robust bulk insert with three-level fallback.
    Returns (ok_bool, inserted_count_estimate)
    """
    if not objs:
        return True, 0
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

    try:
        model_cls = getattr(feedback_handler, "_model", None)
        if model_cls is not None:
            db = feedback_handler.db
            rows = []
            for o in objs:
                if hasattr(o, "model_dump"):
                    rows.append(model_cls(**o.model_dump()))
                else:
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

    # last resort single inserts (resilient to unique violation by skipping)
    inserted = 0
    for o in objs:
        try:
            feedback_handler.create(o)
            inserted += 1
        except Exception as e:
            # minimal logging; continue
            print("single insert failed:", e)
            try:
                feedback_handler.db.rollback()
            except Exception:
                pass
            continue
    return True, inserted

def weighted_sample_without_replacement(items, weights, k):
    """
    Efraimidis-Spirakis weighted sample w/o replacement.
    """
    if k <= 0:
        return []
    if k >= len(items):
        out = items[:]
        random.shuffle(out)
        return out
    eps = 1e-12
    keys = []
    for it, w in zip(items, weights):
        w = max(w, eps)
        u = random.random()
        key = -math.log(u) / w
        keys.append((key, it))
    keys.sort(key=lambda x: x[0])
    return [it for _, it in keys[:k]]

# Main
def generate():
    random.seed(SEED)
    t0 = time.time()
    print("🚀 Starting Synthetic Generator — ALS-optimized (naturalistic)")
    print(f"Target users: {TOTAL_USERS}, Active movies: {ACTIVE_MOVIES}, Clusters: {CLUSTERS}")

    db: Session = next(get_global_db_session())
    user_handler = UserHandler(db)
    feedback_handler = UserFeedbackHandler(db)
    movie_handler = MovieHandler(db)
    auth = AuthService(db)

    # Load full catalog (we will pick ACTIVE_MOVIES subset for generation)
    print("📥 Loading movies from DB (full catalog)...")
    all_movies = movie_handler.list_all(skip=0, limit=10000000)  # hope pagination internally exists
    if not all_movies:
        print("❌ No movies found. Aborting.")
        return

    # Choose active subset for generation (popularity-biased)
    sorted_by_pop = sorted(all_movies, key=lambda m: float(m.popularity or 0.0), reverse=True)
    if len(sorted_by_pop) < ACTIVE_MOVIES:
        print(f"⚠️ Only {len(sorted_by_pop)} movies available; adjusting ACTIVE_MOVIES.")
        active_movies_list = sorted_by_pop
    else:
        candidate_cut = min(len(sorted_by_pop), int(ACTIVE_MOVIES * 1.5))
        candidates = sorted_by_pop[:candidate_cut]
        pops = [max(0.001, float(m.popularity or 1.0)) for m in candidates]
        pow_pops = [p ** 1.2 for p in pops]
        s = sum(pow_pops)
        probs = [p / s for p in pow_pops]
        chosen_indices = set(random.choices(range(len(candidates)), weights=probs, k=ACTIVE_MOVIES))
        chosen = [candidates[i] for i in chosen_indices]
        if len(chosen) < ACTIVE_MOVIES:
            chosen = candidates[:ACTIVE_MOVIES]
        active_movies_list = chosen[:ACTIVE_MOVIES]

    print(f"Active movie pool size (generation subset): {len(active_movies_list)}")

    # maps for generation
    movie_by_id = {m.id: m for m in active_movies_list}
    active_ids = list(movie_by_id.keys())
    pops_active = [max(0.001, float(movie_by_id[mid].popularity or 1.0)) for mid in active_ids]
    pops_active = [p ** 1.2 for p in pops_active]
    s = sum(pops_active) or 1.0
    pop_probs_active = [p / s for p in pops_active]
    id_to_index = {mid: i for i, mid in enumerate(active_ids)}

    # tiers (A/B/C/D)
    tier_a_ids = active_ids[:TIER_A]
    tier_b_ids = active_ids[TIER_A:TIER_A + TIER_B]
    tier_c_ids = active_ids[TIER_A + TIER_B:TIER_A + TIER_B + TIER_C]
    tier_d_ids = active_ids[TIER_A + TIER_B + TIER_C: ACTIVE_MOVIES]

    # extract genres
    genre_counter = Counter()
    movie_genres_map = {}
    for m in active_movies_list:
        gs_raw = []
        if isinstance(m.genres, str):
            gs_raw = [x.strip() for x in m.genres.split(",") if x.strip()]
        elif isinstance(m.genres, list):
            gs_raw = [str(x).strip() for x in m.genres]
        gs = [g for g in gs_raw if g in GENRES]
        movie_genres_map[m.id] = gs
        for g in gs:
            genre_counter[g] += 1

    popular_genres = [g for g, _ in genre_counter.most_common()]
    if len(popular_genres) < 5:
        popular_genres = GENRES[:]
    random.shuffle(popular_genres)

    # cluster genres (2 per cluster)
    cluster_genres = {}
    for ci in range(CLUSTERS):
        g1 = popular_genres[ci % len(popular_genres)]
        g2 = popular_genres[(ci + 7) % len(popular_genres)]
        if g1 == g2:
            g2 = random.choice([x for x in popular_genres if x != g1])
        cluster_genres[ci] = [g1, g2]

    # build clusters with overlap
    shuffled = active_ids[:]
    random.shuffle(shuffled)
    n = len(shuffled)
    pool_size = min(CLUSTER_POOL_SIZE, n)
    step = max(1, int(pool_size * (1 - CLUSTER_POOL_OVERLAP)))
    clusters_info = []
    start = 0
    for ci in range(CLUSTERS):
        pool = []
        for i in range(pool_size):
            idx = (start + i) % n
            pool.append(shuffled[idx])
        start = (start + step) % n
        pool_probs = [pop_probs_active[id_to_index[mid]] for mid in pool]
        s2 = sum(pool_probs) or 1.0
        pool_probs = [p / s2 for p in pool_probs]
        cg = set(cluster_genres[ci])
        for i, mid in enumerate(pool):
            mg = set(movie_genres_map.get(mid, []))
            if mg & cg:
                pool_probs[i] *= 2.0
        s3 = sum(pool_probs) or 1.0
        pool_probs = [p / s3 for p in pool_probs]
        clusters_info.append({"id": ci, "pool": pool, "pool_probs": pool_probs, "genres": cluster_genres[ci]})

    # helper: movie matches prefs
    def movie_matches_prefs(mid, prefs):
        mg = movie_genres_map.get(mid, [])
        if not mg:
            return False
        prefs_set = set([p.lower() for p in prefs])
        for g in mg:
            if g.lower() in prefs_set:
                return True
        return False

    # create users
    print("🧑‍💻 Creating users and assigning clusters...")
    users = []

    # fixed first user
    try:
        print("👤 Creating fixed first user (via AuthService)...")
        fixed_user = auth.register(UserCreate(
            email="rohith.vasu@filmy.com",
            firstname="Rohith",
            lastname="Vasu",
            hashed_password="Password@123",
        ))
        # enforce exactly the requested 5 genres for first user
        fixed_user_prefs = FIRST_USER_PREFS[:]
        # ensure each pref exists in official list
        fixed_user_prefs = [g for g in fixed_user_prefs if g in GENRES]
        # if less than MIN_USER_GENRES somehow, pad from popular_genres
        if len(fixed_user_prefs) < MIN_USER_GENRES:
            extras = [g for g in popular_genres if g not in fixed_user_prefs]
            while len(fixed_user_prefs) < MIN_USER_GENRES and extras:
                fixed_user_prefs.append(extras.pop())
        fixed_user.genre_preferences = ",".join(fixed_user_prefs)
        user_handler.update(fixed_user.id, fixed_user)
        users.append({
            "id": fixed_user.id,
            "cluster": 0,
            "prefs": fixed_user_prefs,
            "strict": True  # mark strict behavior
        })
    except Exception as e:
        print("Failed to create fixed user:", e)

    # create remaining users
    users_per_cluster = math.ceil((TOTAL_USERS - len(users)) / CLUSTERS)
    uid = 2
    for cidx, c in enumerate(tqdm(clusters_info, desc="Clusters")):
        for _ in range(users_per_cluster):
            if len(users) >= TOTAL_USERS:
                break
            try:
                email = f"{fake.user_name()}_{uid}_{random.randint(1000,9999)}@filmy.com"
                user = auth.register(UserCreate(
                    email=email,
                    firstname=fake.first_name(),
                    lastname=fake.last_name(),
                    hashed_password=random_password(),
                ))
                # build prefs: start with cluster's two genres then ensure 4-6
                prefs = list(c["genres"])
                extras = [g for g in popular_genres if g not in prefs]
                random.shuffle(extras)
                while len(prefs) < MIN_USER_GENRES and extras:
                    prefs.append(extras.pop())
                # occasionally add a 5th/6th genre
                while len(prefs) < MAX_USER_GENRES and (random.random() < 0.35):
                    if extras:
                        prefs.append(extras.pop())
                    else:
                        break
                # final padding if still short
                if len(prefs) < MIN_USER_GENRES:
                    pad_candidates = [g for g in GENRES if g not in prefs]
                    random.shuffle(pad_candidates)
                    while len(prefs) < MIN_USER_GENRES and pad_candidates:
                        prefs.append(pad_candidates.pop())
                user.genre_preferences = ",".join(prefs)
                user_handler.update(user.id, user)
                users.append({"id": user.id, "cluster": cidx, "prefs": prefs, "strict": False})
                uid += 1
            except SQLAlchemyError as e:
                print("User creation error:", e)
                try:
                    user_handler.db.rollback()
                except Exception:
                    pass
                continue

    print(f"Created {len(users)} users.")

    # generate feedback
    print("🎯 Generating feedback per user (bulk)...")
    feedback_buffer = []
    total_feedback = 0
    errors = 0
    start_time = time.time()

    def pick_from_pool_with_probs(pool_list, pool_probs, k):
        if k <= 0:
            return []
        weights = [max(1e-12, p) for p in pool_probs]
        return weighted_sample_without_replacement(pool_list, weights, k)

    # For progress stats
    per_user_stats = []

    for u in tqdm(users, desc="Users -> Feedback"):
        user_id = u["id"]
        cluster_id = u["cluster"]
        prefs = u["prefs"]
        is_strict = u.get("strict", False)
        cinfo = clusters_info[cluster_id]
        pool_list = cinfo["pool"]
        pool_probs = cinfo["pool_probs"]

        n_requested = user_interactions_count()

        # If strict first user: interactions must be ONLY from FIRST_USER_PREFS genres
        if is_strict:
            # build pref_candidates strictly from active_ids matching FIRST_USER_PREFS
            pref_candidates = [mid for mid in active_ids if movie_matches_prefs(mid, prefs)]
            if not pref_candidates:
                print(f"WARNING: strict user {user_id} has no matching movies for prefs {prefs}; skipping.")
                continue
            n = min(n_requested, len(pref_candidates))
            # sample without replacement from pref_candidates (no popularity/tail)
            chosen = random.sample(pref_candidates, n)
            final_ids = dedupe_keep_order(chosen)[:n]
            reason = "strict_only_prefs"
        else:
            # naturalistic: allocate k_cluster, k_pop, k_tail
            k_cluster = int(round(n_requested * FRACTION_CLUSTER_POOL))
            k_pop = int(round(n_requested * FRACTION_POPULARITY))
            k_tail = n_requested - (k_cluster + k_pop)
            if k_tail < 0:
                k_tail = 0

            chosen = []

            # 1) cluster picks: allow items both inside and outside prefs
            cluster_candidates = pool_list[:]
            cluster_candidate_probs = pool_probs[:]
            if cluster_candidates and k_cluster > 0:
                picks = pick_from_pool_with_probs(cluster_candidates, cluster_candidate_probs, k_cluster)
                chosen.extend(picks)

            # 2) popularity picks from tiers A/B/C (cross-genre allowed)
            original_pop_pool = []
            original_pop_weights = []
            if tier_a_ids:
                original_pop_pool.extend(tier_a_ids)
                original_pop_weights.extend([3.0] * len(tier_a_ids))
            if tier_b_ids:
                original_pop_pool.extend(tier_b_ids)
                original_pop_weights.extend([1.2] * len(tier_b_ids))
            if tier_c_ids:
                original_pop_pool.extend(tier_c_ids)
                original_pop_weights.extend([0.6] * len(tier_c_ids))

            if original_pop_pool and k_pop > 0:
                picks = weighted_sample_without_replacement(original_pop_pool, original_pop_weights, k_pop)
                chosen.extend(picks)

            # 3) tail picks (tier D) — random exploration
            if tier_d_ids and k_tail > 0:
                tail_pool = tier_d_ids[:]
                tail_weights = [1.0] * len(tail_pool)
                picks = weighted_sample_without_replacement(tail_pool, tail_weights, k_tail)
                chosen.extend(picks)

            # Deduplicate and top-up from active_ids ensuring diversity
            final_ids = dedupe_keep_order(chosen)
            if len(final_ids) < n_requested:
                needed = n_requested - len(final_ids)
                # top-up preferentially from preference candidates, else from active_ids
                pref_candidates = [mid for mid in active_ids if movie_matches_prefs(mid, prefs) and mid not in final_ids]
                if pref_candidates:
                    take = min(len(pref_candidates), needed)
                    final_ids.extend(random.sample(pref_candidates, take))
                    needed = n_requested - len(final_ids)
                if needed > 0:
                    remaining_pool = [mid for mid in active_ids if mid not in final_ids]
                    if remaining_pool:
                        take = min(len(remaining_pool), needed)
                        final_ids.extend(random.sample(remaining_pool, take))
            # final trim
            final_ids = dedupe_keep_order(final_ids)[:n_requested]
            reason = "naturalistic"

        # avoid inserting duplicates already existing in DB for this user
        existing_fbs = feedback_handler.get_user_feedbacks(user_id)
        existing_set = {fb.movie_id for fb in existing_fbs} if existing_fbs else set()
        filtered_ids = [mid for mid in final_ids if mid not in existing_set]

        # top-up if we removed some due to existing entries
        if len(filtered_ids) < len(final_ids):
            needed = len(final_ids) - len(filtered_ids)
            remaining_pool = [mid for mid in active_ids if mid not in filtered_ids and mid not in existing_set]
            if remaining_pool and needed > 0:
                take = min(len(remaining_pool), needed)
                filtered_ids.extend(random.sample(remaining_pool, take))

        filtered_ids = filtered_ids[:len(final_ids)]

        # Build feedback objects and append to buffer
        count_inserted_for_user = 0
        for mid in filtered_ids:
            rating = random.choices(RATING_CHOICES, weights=RATING_WEIGHTS, k=1)[0]
            feedback_buffer.append(make_feedback(user_id, mid, rating))
            total_feedback += 1
            count_inserted_for_user += 1
            if len(feedback_buffer) >= FEEDBACK_BATCH_SIZE:
                ok, inserted = safe_bulk_create(feedback_handler, feedback_buffer)
                if not ok:
                    errors += 1
                feedback_buffer.clear()

        per_user_stats.append({
            "user_id": user_id,
            "n_requested": n_requested,
            "n_final": len(filtered_ids),
            "reason": reason,
            "prefs": prefs
        })

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

    # Print summary stats (small)
    avg_per_user = (total_feedback / len(users)) if users else 0
    print(f"Average feedback per user: {avg_per_user:.1f}")
    # show few user stats
    print("Sample user stats (first 8):")
    for s in per_user_stats[:8]:
        print(s)

if __name__ == "__main__":
    generate()
