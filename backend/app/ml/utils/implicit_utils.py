import os
import pickle
import numpy as np
from typing import List, Dict, Tuple, Any
from scipy.sparse import coo_matrix, save_npz

# Environment / artifact locations
ARTIFACT_DIR = os.getenv("IMPLICIT_ARTIFACT_DIR", "app/ml/models")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "implicit_model.pkl")
DATASET_MAP_PATH = os.path.join(ARTIFACT_DIR, "dataset_map.pkl")
ITEM_FACTORS_PATH = os.path.join(ARTIFACT_DIR, "item_factors.npy")
USER_FACTORS_PATH = os.path.join(ARTIFACT_DIR, "user_factors.npy")
INTERACTIONS_PATH = os.path.join(ARTIFACT_DIR, "interactions.npz")

os.makedirs(ARTIFACT_DIR, exist_ok=True)


def build_interaction_matrix(feedbacks: List[Any],
                             user_map: Dict[int, int],
                             item_map: Dict[int, int],
                             alpha: float = 10.0) -> coo_matrix:
    """
    Build item x user sparse matrix required by implicit (items rows x users cols).
    rating expected in 0.5 - 5.0 increments. status=="watched" without rating -> rating=1.0
    confidence = 1 + alpha * rating
    """
    rows = []
    cols = []
    vals = []

    for f in feedbacks:
        uid = f.user_id
        mid = f.movie_id

        if uid not in user_map or mid not in item_map:
            # skip feedback for users/items we didn't map (keeps trainable space compact)
            continue

        uidx = user_map[uid]
        midx = item_map[mid]

        rating = getattr(f, "rating", None)
        status = getattr(f, "status", None)

        if rating is None:
            if status and str(status).lower() == "watched":
                rating = 1.0
            else:
                # skip non-watched, unrated feedback
                continue

        try:
            rating = float(rating)
        except Exception:
            # skip malformed ratings
            continue

        # convert rating to confidence (positive)
        confidence = 1.0 + alpha * rating
        rows.append(midx)    # item index (row)
        cols.append(uidx)    # user index (col)
        vals.append(confidence)

    num_items = len(item_map)
    num_users = len(user_map)
    mat = coo_matrix((vals, (rows, cols)), shape=(num_items, num_users))
    return mat


def save_artifacts(model, dataset_map: Dict[str, Dict[int, int]], interactions: coo_matrix):
    """Save model, maps, factors and interactions to disk."""
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    # Save model with pickle
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    with open(DATASET_MAP_PATH, "wb") as f:
        pickle.dump(dataset_map, f)

    # Save factors (model should have item_factors and user_factors if trained)
    try:
        np.save(ITEM_FACTORS_PATH, model.item_factors)
        np.save(USER_FACTORS_PATH, model.user_factors)
    except Exception:
        # some implicit versions expose factors in different names; try attributes
        if hasattr(model, "factors"):
            np.save(ITEM_FACTORS_PATH, model.factors)
        else:
            raise

    # Save interactions matrix for reproducibility
    save_npz(INTERACTIONS_PATH, interactions.tocsr())
