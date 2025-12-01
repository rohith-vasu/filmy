from mlflow.tracking import MlflowClient

client = MlflowClient()

def auto_promote_if_better(
    run_id: str,
    model_name: str,
    metric_name: str = "precision_at_10",
):
    """
    Promote this run to Production **if it's better than current production**.
    """

    # Get the metric of the current run
    run = client.get_run(run_id)
    new_metric = run.data.metrics.get(metric_name)
    if new_metric is None:
        print("❌ No metric found for new model. Skipping promotion.")
        return

    # Get current production model (if exists)
    versions = client.search_model_versions(f"name='{model_name}' and current_stage='Production'")

    if len(versions) == 0:
        print("🚀 No production model found — promoting new model as Production.")
        client.transition_model_version_stage(
            name=model_name,
            version=client.get_latest_versions(model_name, stages=[])[-1].version,
            stage="Production"
        )
        return

    prod_version = versions[0]
    prod_run_id = prod_version.run_id
    prod_run = client.get_run(prod_run_id)
    old_metric = prod_run.data.metrics.get(metric_name, 0)

    print(f"🧠 Prod metric: {old_metric}, New metric: {new_metric}")

    if new_metric > old_metric:
        print("🔥 New model is better → PROMOTING to Production...")
        client.transition_model_version_stage(
            name=model_name,
            version=prod_version.version + 1,
            stage="Production"
        )
    else:
        print("📉 New model worse → Keeping existing Production.")

def archive_old_versions(model_name: str, keep_last: int = 3):
    versions = client.search_model_versions(f"name='{model_name}'")

    # Sort by version number
    versions = sorted(versions, key=lambda v: int(v.version), reverse=True)

    for v in versions[keep_last:]:
        print(f"📦 Archiving old version {v.version}")
        client.transition_model_version_stage(
            name=model_name,
            version=v.version,
            stage="Archived"
        )

def delete_model_versions(model_name: str, keep_last: int = 5):
    versions = client.search_model_versions(f"name='{model_name}'")

    versions = sorted(versions, key=lambda v: int(v.version), reverse=True)

    for v in versions[keep_last:]:
        print(f"🗑 Deleting version {v.version}")
        client.delete_model_version(
            name=model_name,
            version=v.version
        )