import os
import pickle
import numpy as np
from typing import List
from scipy.sparse import coo_matrix, save_npz
from tqdm import tqdm

from app.model_handlers.user_feedback_handler import UserFeedbackHandler, UserFeedbackResponse


# ---------------------------------------------------------
# Load feedback
# ---------------------------------------------------------
def load_feedbacks_from_db(db) -> List[UserFeedbackResponse]:
    handler = UserFeedbackHandler(db)
    return handler.list_all(limit=2000000)


# ---------------------------------------------------------
# Dataset maps
# ---------------------------------------------------------
def build_dataset_map(feedbacks: List[UserFeedbackResponse]):
    user_ids = sorted({fb.user_id for fb in feedbacks})
    item_ids = sorted({fb.movie_id for fb in feedbacks})

    user_map = {uid: i for i, uid in enumerate(user_ids)}
    item_map = {mid: i for i, mid in enumerate(item_ids)}
    inv_item_map = {i: mid for mid, i in item_map.items()}

    return {
        "user_map": user_map,
        "item_map": item_map,
        "inv_item_map": inv_item_map,
    }


# ---------------------------------------------------------
# Interaction Matrix
# ---------------------------------------------------------
def build_interaction_matrix(feedbacks, user_map, item_map, alpha=10.0):
    rows, cols, vals = [], [], []

    for fb in feedbacks:
        if fb.user_id not in user_map or fb.movie_id not in item_map:
            continue

        rating = float(fb.rating) if fb.rating else 1.0
        confidence = 1.0 + alpha * rating

        rows.append(user_map[fb.user_id])
        cols.append(item_map[fb.movie_id])
        vals.append(confidence)

    return coo_matrix(
        (vals, (rows, cols)),
        shape=(len(user_map), len(item_map))
    )


# ---------------------------------------------------------
# Save artifacts
# ---------------------------------------------------------
def save_artifacts_to_tempdir(model, dataset_map, interactions, temp_dir="/tmp/implicit_artifacts"):
    os.makedirs(temp_dir, exist_ok=True)

    with open(os.path.join(temp_dir, "implicit_model.pkl"), "wb") as f:
        pickle.dump(model, f)

    with open(os.path.join(temp_dir, "dataset_map.pkl"), "wb") as f:
        pickle.dump(dataset_map, f)

    np.save(os.path.join(temp_dir, "item_factors.npy"), model.item_factors)
    np.save(os.path.join(temp_dir, "user_factors.npy"), model.user_factors)

    save_npz(os.path.join(temp_dir, "interactions.npz"), interactions.tocsr())

    return temp_dir


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------
def evaluate_model(model, interactions, dataset_map, sample_users=2000):
    item_user = interactions.tocsc()
    num_items, num_users = item_user.shape

    valid_items = model.item_factors.shape[0]

    user_pos = {}
    for uid in range(num_users):
        items = item_user[:, uid].nonzero()[0]
        items = [i for i in items if i < valid_items]
        if len(items) >= 2:
            user_pos[uid] = items

    if not user_pos:
        return 0.0, 0.0

    users = list(user_pos.keys())
    if len(users) > sample_users:
        users = list(np.random.choice(users, sample_users, replace=False))

    preds, truths = [], []

    for u in tqdm(users, desc="Eval users"):
        pos_items = user_pos[u]
        test_item = pos_items[-1]
        train_items = set(pos_items[:-1])

        uvec = model.user_factors[u]
        scores = model.item_factors.dot(uvec)

        # mask training items
        for it in train_items:
            if it < len(scores):
                scores[it] = -np.inf

        top_k = np.argsort(-scores)[:100]
        preds.append(top_k)
        truths.append({test_item})

    def precision_at_k(k=10):
        return np.mean([
            len(set(top[:k]) & true) / k 
            for top, true in zip(preds, truths)
        ])

    def recall_at_k(k=10):
        return np.mean([
            len(set(top[:k]) & true) / len(true)
            for top, true in zip(preds, truths)
        ])

    return precision_at_k(), recall_at_k()
