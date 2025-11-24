import os
import pickle
import numpy as np
from app.ml.utils.implicit_utils import (
    ARTIFACT_DIR,
)

MODEL_PATH = os.path.join(ARTIFACT_DIR, "implicit_model.pkl")
DATASET_MAP_PATH = os.path.join(ARTIFACT_DIR, "dataset_map.pkl")
ITEM_FACTORS_PATH = os.path.join(ARTIFACT_DIR, "item_factors.npy")
USER_FACTORS_PATH = os.path.join(ARTIFACT_DIR, "user_factors.npy")


def load_implicit_artifacts():
    """Return model, dataset_map, item_factors, user_factors or (None,..) if missing."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(DATASET_MAP_PATH):
        return None, None, None, None

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    with open(DATASET_MAP_PATH, "rb") as f:
        dataset_map = pickle.load(f)

    # load factor arrays if saved
    item_factors = None
    user_factors = None
    if os.path.exists(ITEM_FACTORS_PATH):
        item_factors = np.load(ITEM_FACTORS_PATH, allow_pickle=False)
    if os.path.exists(USER_FACTORS_PATH):
        user_factors = np.load(USER_FACTORS_PATH, allow_pickle=False)

    return model, dataset_map, item_factors, user_factors
