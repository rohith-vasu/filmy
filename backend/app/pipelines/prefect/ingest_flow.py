from prefect import flow, task, get_run_logger
from app.pipelines.data.ingest_tmdb import run_daily_ingest


@task
def ingest_task():
    logger = get_run_logger()
    res = run_daily_ingest()
    logger.info(f"Ingest Result: {res}")
    return res


@flow(name="ingest_flow")
def run_ingest():
    ingest_task()


if __name__ == "__main__":
    run_ingest()
