import os
import json
import subprocess
from minio import Minio
import s3fs
from loguru import logger

from app.core.settings import settings

MINIO_ENDPOINT = settings.minio.endpoint
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() in ("1", "true", "yes")
DATA_BUCKET = settings.minio.data_bucket
DVC_REMOTE = settings.dvc.remote

# s3fs filesystem
def get_s3fs():
    return s3fs.S3FileSystem(
        key=MINIO_ACCESS_KEY,
        secret=MINIO_SECRET_KEY,
        client_kwargs={"endpoint_url": f"http://{MINIO_ENDPOINT}"},
        config_kwargs={"s3": {"addressing_style": "virtual"}}
    )

# MinIO client (for small metadata)
def get_minio_client():
    return Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )

def upload_local_file_to_minio(local_path: str, object_name: str, bucket: str = DATA_BUCKET):
    """Uploads a local file path to MinIO using minio client."""
    client = get_minio_client()
    found = client.bucket_exists(bucket)
    if not found:
        client.make_bucket(bucket)
    client.fput_object(bucket, object_name, local_path)
    logger.info("Uploaded %s to s3://%s/%s", local_path, bucket, object_name)

def write_obj_to_minio(obj: dict, object_name: str, bucket: str = DATA_BUCKET):
    client = get_minio_client()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    client.put_object(bucket, object_name, data=json.dumps(obj).encode("utf-8"),
                      length=len(json.dumps(obj).encode("utf-8")), content_type="application/json")
    logger.info("Wrote JSON to s3://%s/%s", bucket, object_name)

def read_json_from_minio(object_name: str, bucket: str = DATA_BUCKET):
    client = get_minio_client()
    try:
        resp = client.get_object(bucket, object_name)
        data = resp.read().decode("utf-8")
        return json.loads(data)
    except Exception:
        return None

# DVC helper: configure remote to MinIO (call once)
def dvc_config_remote():
    # Assumes dvc installed and repo root is working dir
    endpoint = f"http://{MINIO_ENDPOINT}"
    cmds = [
        ["dvc", "remote", "add", "-d", DVC_REMOTE, f"s3://filmy-dvc"],
        ["dvc", "remote", "modify", DVC_REMOTE, "endpointurl", endpoint],
        ["dvc", "remote", "modify", DVC_REMOTE, "access_key_id", MINIO_ACCESS_KEY],
        ["dvc", "remote", "modify", DVC_REMOTE, "secret_access_key", MINIO_SECRET_KEY],
        ["dvc", "remote", "modify", DVC_REMOTE, "use_ssl", "false"]
    ]
    for cmd in cmds:
        subprocess.run(cmd, check=False)
    logger.info("Configured DVC remote '%s' to MinIO at %s", DVC_REMOTE, endpoint)

# utility to run dvc add/push
def dvc_add_and_push(path: str):
    subprocess.run(["dvc", "add", path], check=True)
    subprocess.run(["git", "add", f"{path}.dvc"], check=False)
    subprocess.run(["git", "commit", "-m", f"Add data snapshot {path}"], check=False)
    subprocess.run(["dvc", "push"], check=True)
    logger.info("DVC added and pushed %s", path)
