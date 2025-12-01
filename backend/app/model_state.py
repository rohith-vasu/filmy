from app.utils.model_loader import load_latest_production_model
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Global shared model cache in memory
MODEL_CACHE = {
    "implicit_model": None,
    "dataset_map": None,
    "item_factors": None,
    "user_factors": None,
    "model_version": None,
}

EURO_TZ = ZoneInfo("Europe/Paris")


def load_model():
    """Load the MLflow production model into global cache."""
    model, dataset_map, item_factors, user_factors, run_id = load_latest_production_model()

    MODEL_CACHE["implicit_model"] = model
    MODEL_CACHE["dataset_map"] = dataset_map
    MODEL_CACHE["item_factors"] = item_factors
    MODEL_CACHE["user_factors"] = user_factors

    # Save the run_id as version identifier
    MODEL_CACHE["model_version"] = run_id

    print(f"✅ Model loaded (version={MODEL_CACHE['model_version']})")
    return MODEL_CACHE


def seconds_until_next_4am():
    """Calculate seconds until next 4 AM Europe/Paris time."""
    now = datetime.now(EURO_TZ)
    tomorrow = now + timedelta(days=1)
    next_run = now.replace(hour=4, minute=0, second=0, microsecond=0)

    if now >= next_run:
        next_run = tomorrow.replace(hour=4, minute=0, second=0, microsecond=0)

    return (next_run - now).total_seconds()


def model_watcher_thread():
    """Background thread: checks for new models daily at 4 AM."""
    import time
    from app.utils.model_loader import load_latest_production_model

    while True:
        sleep_secs = seconds_until_next_4am()
        print(f"⏳ Sleeping for {sleep_secs/3600:.2f} hours until next 4 AM reload...")

        time.sleep(sleep_secs)

        print("🔄 4 AM reached — checking MLflow for new model...")
        new_model, _, _, _ = load_latest_production_model()
        new_version = new_model._model_impl.metadata.run_id

        if MODEL_CACHE["model_version"] != new_version:
            print(f"🔥 New model detected: {new_version} — reloading...")
            load_model()
        else:
            print("✔ No new model available — using existing model.")
