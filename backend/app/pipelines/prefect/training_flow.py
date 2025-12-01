import os
import psycopg2
from datetime import datetime

from prefect import flow, task, get_run_logger
import mlflow

from app.core.settings import settings
from app.pipelines.training.train_implicit import train

DB_USER = settings.db.username
DB_PASS = settings.DB_PASSWORD
DB_HOST = settings.db.host
DB_NAME = settings.db.database
DB_PORT = settings.db.port

POSTGRES_DSN = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "filmy_implicit_training")

THRESHOLD = 100


# ---------------------------------------------------------
# Helper: Get timestamp of last successful MLflow training run
# ---------------------------------------------------------
def get_last_training_time_from_mlflow():
    mlflow.set_tracking_uri(MLFLOW_URI)
    exp = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT)

    if exp is None:
        return None  # no experiment yet

    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["attribute.start_time DESC"],
        max_results=1,
    )

    if len(runs) == 0:
        return None

    last_start_time = runs.iloc[0]["start_time"].to_pydatetime()
    return last_start_time


# ---------------------------------------------------------
# Helper: count new feedback since last train
# ---------------------------------------------------------
def get_new_feedback_count(conn, last_train_time):
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*) 
        FROM user_feedback
        WHERE created_at > %s;
        """,
        (last_train_time,),
    )

    count = cur.fetchone()[0]
    return count


# ---------------------------------------------------------
# Prefect Task: train only if enough new feedback
# ---------------------------------------------------------
@task
def train_if_needed():
    logger = get_run_logger()

    # 1. Get last training time from MLflow
    last_train_time = get_last_training_time_from_mlflow()

    if last_train_time is None:
        logger.info("No previous training run found in MLflow → training now.")
        return train()

    logger.info(f"Last training time (from MLflow): {last_train_time}")

    # 2. Count new feedback rows since last training
    conn = psycopg2.connect(POSTGRES_DSN)
    new_count = get_new_feedback_count(conn, last_train_time)
    conn.close()

    logger.info(f"New feedback since last training: {new_count}")

    # 3. Only train if threshold reached
    if new_count >= THRESHOLD:
        logger.info(f"Threshold reached ({new_count} ≥ {THRESHOLD}) → training model.")
        return train()

    logger.info(f"Only {new_count} new feedback rows (< {THRESHOLD}) → skipping training.")
    return None


# ---------------------------------------------------------
# Prefect Flow
# ---------------------------------------------------------
@flow(name="training_flow")
def run_train():
    train_if_needed()


if __name__ == "__main__":
    run_train()
