# download_model.py

import os
from dotenv import load_dotenv
from app.utils import download_model_from_s3

load_dotenv()

BUCKET_NAME = os.getenv("MODEL_BUCKET")
MODEL_S3_KEY = "model/latest_model.json"
MODEL_DIR = os.getenv("MODEL_DIR", "/home/ec2-user/mlops-api/model")

if __name__ == "__main__":
    download_model_from_s3(
        bucket_name=BUCKET_NAME,
        s3_key=MODEL_S3_KEY,
        model_dir=MODEL_DIR
    )
