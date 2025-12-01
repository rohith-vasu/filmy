import os
import json
import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
import numpy as np
from loguru import logger
from implicit.als import AlternatingLeastSquares

from app.core.settings import settings
from app.core.db import get_global_db_session
from app.pipelines.training.training_helper import (
    load_feedbacks_from_db,
    build_dataset_map,
    build_interaction_matrix,
    save_artifacts_to_tempdir,
    evaluate_model
)
from app.pipelines.training.als_mlflow_wrapper import ALSModelWrapper


# --------------------------
# Hyperparameters
# --------------------------
FACTORS = settings.mlflow.factors
REGULARIZATION = settings.mlflow.regularization
ALPHA = settings.mlflow.alpha
EPOCHS = settings.mlflow.epochs

MLFLOW_EXPERIMENT = settings.mlflow.experiment
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5500")

ARTIFACT_TEMP_DIR = "/tmp/implicit_artifacts"

# Load synthetic config JSON
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "generate_config.json"))
DATA_CONFIG = json.load(open(CONFIG_PATH))


# ------------------------------------------
# Helper: Get current production model stats
# ------------------------------------------
def get_current_production_metrics(model_name="filmy_implicit_model"):
    client = MlflowClient()
    versions = client.search_model_versions(
        f"name='{model_name}' and tags.stage='production'"
    )

    if not versions:
        return None, None, None  # No production model yet

    v = versions[0]
    run = mlflow.get_run(v.run_id)

    p10 = run.data.metrics.get("precision_at_10")
    r10 = run.data.metrics.get("recall_at_10")

    return v, p10, r10


def is_better(new_p10, new_r10, old_p10, old_r10):
    """Return True if new model clearly outperforms production."""
    # No production model yet → promote unconditionally
    if old_p10 is None or old_r10 is None:
        return True

    # Strict: must exceed precision AND at least match recall
    return (new_p10 > old_p10) and (new_r10 >= old_r10)


# ------------------------------------------
# TRAIN FUNCTION
# ------------------------------------------
def train():
    logger.info("Connecting to database...")
    db = next(get_global_db_session())

    # Load feedback
    feedbacks = load_feedbacks_from_db(db)
    logger.info(f"Loaded {len(feedbacks)} feedback rows")

    # Build maps
    dataset_map = build_dataset_map(feedbacks)
    user_map = dataset_map["user_map"]
    item_map = dataset_map["item_map"]

    # Sparse matrix
    interactions = build_interaction_matrix(
        feedbacks, user_map, item_map, alpha=ALPHA
    )

    # MLflow setup
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    with mlflow.start_run(run_name="implicit_als") as run:
        run_id = run.info.run_id
        logger.info(f"Run ID = {run_id}")

        # Log config + params
        mlflow.log_params({f"data_{k}": v for k, v in DATA_CONFIG.items()})
        mlflow.log_params({
            "factors": FACTORS,
            "regularization": REGULARIZATION,
            "epochs": EPOCHS,
            "alpha": ALPHA,
            "n_users": len(user_map),
            "n_items": len(item_map),
        })

        # Train ALS
        logger.info("Training ALS model...")
        model = AlternatingLeastSquares(
            factors=FACTORS,
            regularization=REGULARIZATION,
            iterations=EPOCHS,
            use_gpu=False,
        )
        model.fit(interactions.tocsr(), show_progress=True)

        # Evaluation
        p10, r10 = evaluate_model(model, interactions, dataset_map)
        mlflow.log_metric("precision_at_10", p10)
        mlflow.log_metric("recall_at_10", r10)

        # Save artifacts
        artifact_dir = save_artifacts_to_tempdir(
            model, dataset_map, interactions, ARTIFACT_TEMP_DIR
        )
        mlflow.log_artifacts(artifact_dir)

        # Register Model
        conda_env = mlflow.pyfunc.get_default_conda_env()
        input_example = np.random.rand(1, FACTORS)
        signature = mlflow.models.infer_signature(
            input_example, input_example @ np.random.rand(FACTORS, FACTORS)
        )

        mlflow.pyfunc.log_model(
            name="als_model",
            python_model=ALSModelWrapper(),
            registered_model_name="filmy_implicit_model",
            conda_env=conda_env,
            signature=signature,
            input_example=input_example,
            artifacts={
                "implicit_model": os.path.join(artifact_dir, "implicit_model.pkl"),
                "dataset_map": os.path.join(artifact_dir, "dataset_map.pkl"),
                "user_factors": os.path.join(artifact_dir, "user_factors.npy"),
                "item_factors": os.path.join(artifact_dir, "item_factors.npy"),
            },
        )

        logger.info("Model logged in MLflow registry")

        # Get newly logged version
        client = MlflowClient()
        versions = client.search_model_versions("name='filmy_implicit_model'")
        latest = max(versions, key=lambda v: int(v.version))

        # Compare with production
        prod_version, prod_p10, prod_r10 = get_current_production_metrics()

        logger.info(f"Production p10={prod_p10}, r10={prod_r10}")
        logger.info(f"New p10={p10}, r10={r10}")

        if is_better(p10, r10, prod_p10, prod_r10):
            logger.info("🎉 New model outperforms production → promoting")

            # Promote new model
            client.set_model_version_tag(
                name="filmy_implicit_model",
                version=latest.version,
                key="stage",
                value="production"
            )

            # Remove tag from old model
            if prod_version:
                client.delete_model_version_tag(
                    name="filmy_implicit_model",
                    version=prod_version.version,
                    key="stage"
                )

            logger.info(f"🔥 Model v{latest.version} promoted to PRODUCTION")
        else:
            logger.info("❌ New model NOT better → skip promotion")

    logger.info("Training complete.")
    return run_id


if __name__ == "__main__":
    train()
