import os
import numpy as np
from tqdm import tqdm
import mlflow

from implicit.als import AlternatingLeastSquares
from scipy.sparse import coo_matrix

from app.core.db import get_global_db_session
from app.model_handlers.movie_handler import MovieHandler
from app.model_handlers.user_feedback_handler import UserFeedbackHandler
from app.ml.utils.implicit_utils import (
    build_interaction_matrix,
    save_artifacts,
    ARTIFACT_DIR
)

# Config via env
FACTORS = int(os.getenv("IMPLICIT_FACTORS", 64))
REGULARIZATION = float(os.getenv("IMPLICIT_REG", 0.01))
ALPHA = float(os.getenv("IMPLICIT_ALPHA", 10.0))
EPOCHS = int(os.getenv("IMPLICIT_EPOCHS", 20))
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "implicit_training")
SAMPLE_EVAL_USERS = int(os.getenv("IMPLICIT_EVAL_SAMPLE_USERS", 2000))


def build_maps_and_feedbacks(db):
    """Return dataset map and list of feedback objects"""
    movie_handler = MovieHandler(db)
    fb_handler = UserFeedbackHandler(db)

    # load all feedbacks first
    feedbacks = fb_handler.list_all(limit=1000000)
    if not feedbacks:
        raise RuntimeError("No feedback rows found in DB - cannot train model.")

    # Build user map (only users present in feedbacks)
    user_ids = sorted({f.user_id for f in feedbacks})
    user_map = {uid: idx for idx, uid in enumerate(user_ids)}
    inv_user_map = {idx: uid for uid, idx in user_map.items()}

    # Keep only items that appear at least once in feedbacks
    item_ids_with_feedback = sorted({f.movie_id for f in feedbacks})
    item_map = {mid: idx for idx, mid in enumerate(item_ids_with_feedback)}
    inv_item_map = {idx: mid for mid, idx in item_map.items()}

    dataset_map = {
        "user_map": user_map,
        "item_map": item_map,
        "inv_item_map": inv_item_map,
    }
    return dataset_map, feedbacks


def evaluate(model, interactions: coo_matrix, dataset_map: dict):
    """
    Simple leave-one-out evaluation on a sample of users.
    Avoids using items not present in model.item_factors.
    """
    item_user = interactions.tocsc()
    num_items, num_users = item_user.shape
    valid_item_count = model.item_factors.shape[0]

    # Build per-user positive item sets but only for valid items
    user_pos = {}
    for uid in range(num_users):
        item_idxs = item_user[:, uid].nonzero()[0].tolist()
        # keep only valid items (trained)
        item_idxs = [it for it in item_idxs if it < valid_item_count]
        user_pos[uid] = item_idxs

    # sample users for eval if needed
    user_list = [u for u in range(num_users) if len(user_pos.get(u, [])) >= 2]
    if not user_list:
        print("No users with >=2 interactions for evaluation.")
        return

    if len(user_list) > SAMPLE_EVAL_USERS:
        user_list = list(np.random.choice(user_list, SAMPLE_EVAL_USERS, replace=False))

    preds = []
    truths = []
    for u in tqdm(user_list, desc="Eval users"):
        pos = user_pos[u]
        # holdout last item
        test_item = pos[-1]
        train_items = set(pos[:-1])

        user_vec = model.user_factors[u]
        scores = model.item_factors.dot(user_vec)

        # mask train items
        for it in train_items:
            if it < len(scores):
                scores[it] = -np.inf

        topk = np.argsort(-scores)[:100]
        preds.append(topk)
        truths.append({test_item})

    # compute precision@10 and recall@10
    def precision_at_k(preds_list, truths_list, k=10):
        ps = []
        for p, t in zip(preds_list, truths_list):
            hit = len(set(p[:k]) & t)
            ps.append(hit / k)
        return np.mean(ps) if ps else 0.0

    def recall_at_k(preds_list, truths_list, k=10):
        rs = []
        for p, t in zip(preds_list, truths_list):
            hit = len(set(p[:k]) & t)
            rs.append(hit / len(t))
        return np.mean(rs) if rs else 0.0

    p10 = precision_at_k(preds, truths, k=10)
    r10 = recall_at_k(preds, truths, k=10)

    mlflow.log_metric("precision_at_10", float(p10))
    mlflow.log_metric("recall_at_10", float(r10))
    print(f"Eval -> precision_at_10={p10:.4f}, recall_at_10={r10:.4f}")


def train():
    db = next(get_global_db_session())
    dataset_map, feedbacks = build_maps_and_feedbacks(db)
    print(f"Users: {len(dataset_map['user_map'])}, Items: {len(dataset_map['item_map'])}, Feedbacks: {len(feedbacks)}")

    # Build interactions (item x user)
    interactions = build_interaction_matrix(feedbacks, dataset_map["user_map"], dataset_map["item_map"], alpha=ALPHA)

    # MLflow
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    with mlflow.start_run(run_name="implicit_als"):
        mlflow.log_param("factors", FACTORS)
        mlflow.log_param("regularization", REGULARIZATION)
        mlflow.log_param("alpha", ALPHA)
        mlflow.log_param("epochs", EPOCHS)

        model = AlternatingLeastSquares(factors=FACTORS, regularization=REGULARIZATION, iterations=EPOCHS, use_gpu=False)

        print("Fitting implicit ALS model...")
        model.fit(interactions.tocsr(), show_progress=True)

        print("Saving artifacts...")
        save_artifacts(model, dataset_map, interactions)

        # evaluate
        print("Evaluating model...")
        evaluate(model, interactions, dataset_map)

        mlflow.log_artifacts(ARTIFACT_DIR)
        print("Artifacts logged to", ARTIFACT_DIR)

    print("Training complete.")


if __name__ == "__main__":
    train()
